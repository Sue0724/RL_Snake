"""Author editable native Office objects, then embed native OOXML charts."""
from io import BytesIO
from pathlib import Path
import json
import re
import zipfile
import xml.etree.ElementTree as ET

import win32com.client
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / '.ppt_build'
OUT = ROOT / 'deliverables'
OUT.mkdir(exist_ok=True)
FONT = 'Microsoft YaHei'
GREEN = '16856A'
CORAL = 'D97568'
INK = '25352F'
GRAY = '61716A'
LIGHT = 'EAF4EF'
LINE = 'DCE6E0'
WHITE = 'FFFFFF'
TIMES = [20, 40, 50, 55, 45, 50, 50, 45, 60, 45, 75, 35]
OWNERS = ['A'] * 3 + ['B'] * 2 + ['C'] * 2 + ['D'] * 5
GEOMETRY = []


def rgb(h):
    return int(h[:2], 16) + (int(h[2:4], 16) << 8) + (int(h[4:], 16) << 16)


app = win32com.client.DispatchEx('PowerPoint.Application')
p = app.Presentations.Add(0)
p.PageSetup.SlideWidth = 960
p.PageSetup.SlideHeight = 540


def text(slide, content, x, y, w, h, size=22, color=INK, bold=False, align=1):
    sh = slide.Shapes.AddTextbox(1, x, y, w, h)
    sh.Name = 'Text_' + str(slide.Shapes.Count)
    tf = sh.TextFrame
    tf.MarginLeft = tf.MarginRight = 0
    tf.MarginTop = tf.MarginBottom = 0
    tf.WordWrap = -1
    tr = tf.TextRange
    tr.Text = content
    tr.Font.Name = FONT
    try:
        tr.Font.NameFarEast = FONT
    except Exception:
        pass
    tr.Font.Size = size
    tr.Font.Color.RGB = rgb(color)
    tr.Font.Bold = -1 if bold else 0
    tr.ParagraphFormat.Alignment = align
    try:
        tr.ParagraphFormat.SpaceAfter = 6
    except Exception:
        pass
    GEOMETRY.append({'slide': slide.SlideIndex, 'text': content, 'x': x, 'y': y,
                     'w': w, 'h': h, 'bound_h': float(tr.BoundHeight), 'size': size})
    return sh


def rect(slide, x, y, w, h, fill=LIGHT, border=None):
    sh = slide.Shapes.AddShape(1, x, y, w, h)
    sh.Fill.Solid()
    sh.Fill.ForeColor.RGB = rgb(fill)
    sh.Line.Visible = -1 if border else 0
    if border:
        sh.Line.ForeColor.RGB = rgb(border)
        sh.Line.Weight = .7
    return sh


def line(slide, x1, y1, x2, y2, color=LINE, arrow=False):
    sh = slide.Shapes.AddLine(x1, y1, x2, y2)
    sh.Line.ForeColor.RGB = rgb(color)
    sh.Line.Weight = 1.4
    if arrow:
        sh.Line.EndArrowheadStyle = 3
    return sh


def notes(slide, script, caution='', source='ppt.md'):
    i = slide.SlideIndex - 1
    content = (f'汇报人：{OWNERS[i]}\n建议时长：{TIMES[i]} 秒\n\n讲稿：\n{script}'
               + (f'\n\n补充说明：\n{caution}' if caution else '')
               + f'\n\n项目事实来源：{source}。页内统计均以项目正式实验记录为准。')
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = content


def slide(title, sub=''):
    s = p.Slides.Add(p.Slides.Count + 1, 12)
    s.FollowMasterBackground = 0
    s.Background.Fill.Solid()
    s.Background.Fill.ForeColor.RGB = rgb(WHITE)
    text(s, title, 48, 35, 864, 48, 30, bold=True)
    if sub:
        text(s, sub, 48, 92, 864, 32, 18, GRAY)
    text(s, f'{s.SlideIndex:02d}', 866, 505, 46, 20, 12, GRAY, align=3)
    return s


def board(s, x, y, size, local=False):
    cell = size / 10
    head = (5, 5)
    snake = [(5, 5), (5, 4), (5, 3), (6, 3), (7, 3), (7, 2)]
    for row in range(10):
        for col in range(10):
            fill = WHITE
            if local and abs(row - head[0]) <= 1 and abs(col - head[1]) <= 1:
                fill = 'D5EBE0'
            if (row, col) in snake:
                fill = GREEN if (row, col) == head else '81B9A2'
            if (row, col) == (2, 7):
                fill = CORAL
            rect(s, x + col * cell, y + row * cell, cell, cell, fill, LINE)
    # The cell diagram is intentionally editable and explicitly illustrative.
    text(s, '环境示意', x, y + size + 12, size, 26, 16, GRAY, align=2)


def table(s, rows, x, y, w, h, widths=None, fs=21):
    sh = s.Shapes.AddTable(len(rows), len(rows[0]), x, y, w, h)
    tb = sh.Table
    if widths:
        for j, width in enumerate(widths, 1):
            tb.Columns(j).Width = width
    for i, row in enumerate(rows, 1):
        for j, value in enumerate(row, 1):
            ce = tb.Cell(i, j).Shape
            ce.Fill.Solid()
            ce.Fill.ForeColor.RGB = rgb(LIGHT if i == 1 else WHITE)
            tf = ce.TextFrame
            tf.MarginLeft = 12
            tf.MarginRight = 8
            tf.MarginTop = 7
            tf.MarginBottom = 5
            tf.VerticalAnchor = 3
            tr = tf.TextRange
            tr.Text = str(value)
            tr.Font.Name = FONT
            try:
                tr.Font.NameFarEast = FONT
            except Exception:
                pass
            tr.Font.Size = fs
            tr.Font.Color.RGB = rgb(GREEN if i == 1 else INK)
            tr.Font.Bold = -1 if i == 1 else 0
            for b in (1, 2, 3, 4):
                tb.Cell(i, j).Borders(b).ForeColor.RGB = rgb(LINE)
                tb.Cell(i, j).Borders(b).Weight = .5
    return sh


def node(s, label, x, y, w=160, h=64, color=LIGHT):
    rect(s, x, y, w, h, color)
    text(s, label, x + 8, y + 12, w - 16, h - 20, 21, GREEN, True, 2)


def chart_anchor(s, name, x=48, y=148, w=520, h=304):
    sh = rect(s, x, y, w, h, WHITE)
    sh.Name = name


try:
    s = slide('')
    text(s, '基于深度强化学习的\n贪吃蛇智能体', 48, 105, 575, 112, 36, bold=True)
    text(s, '设计与实验研究', 48, 231, 550, 48, 28, GREEN, True)
    text(s, 'DQN / Double DQN / Dueling DQN', 48, 307, 585, 38, 22, GRAY)
    text(s, '强化学习课程小组汇报', 48, 380, 560, 32, 20)
    text(s, '潘明东、张欣怡、张娄瑞、周欣语', 48, 424, 580, 32, 19)
    text(s, '2026 年 10 月', 48, 468, 400, 28, 18, GRAY)
    board(s, 660, 150, 230)
    notes(s, '各位老师、同学好。我们在自建贪吃蛇环境中实现三种DQN算法，研究哪些状态、奖励和探索设计能让智能体吃到更多食物。下面先介绍环境，再介绍算法和实验结果。')

    s = slide('环境与强化学习建模', '稀疏反馈与动态蛇身，使简单规则形成长期决策问题')
    board(s, 48, 157, 270)
    text(s, '10×10 棋盘，初始蛇长 3\n动作：直行、左转、右转\n奖励：食物 +10，死亡 −10，移动 0', 374, 155, 538, 126, 22)
    node(s, '观测', 374, 320, 140)
    node(s, '动作', 570, 320, 140)
    node(s, '奖励 / 新观测', 766, 320, 146)
    line(s, 522, 352, 559, 352, GREEN, True)
    line(s, 718, 352, 755, 352, GREEN, True)
    text(s, '碰撞或满盘：终止\n达到 500 步：截断', 374, 412, 538, 65, 20, GRAY)
    notes(s, '棋盘是十乘十，初始蛇长三，智能体每步选择直行、左转或右转。基础奖励只在吃到食物或死亡时出现，因此反馈稀疏。随着蛇身增长，可走空间也在变化，这要求考虑长期后果。所有算法共用环境。碰撞或满盘是真终止，达到五百步只是截断。', '完整游戏状态可以描述MDP，但人工压缩观测不保证完整马尔可夫性。', 'docs/INTERFACE.md')

    s = slide('状态表示：11 维与 20 维', 'V1 提供紧凑基线，V2 增加距离与相对局部障碍')
    text(s, 'V1   11 维', 48, 158, 500, 44, 28, GREEN, True)
    text(s, '危险 3 + 朝向 4 + 食物方位 4', 48, 213, 560, 42, 22)
    text(s, 'V2   11 + 1 + 8 = 20 维', 48, 291, 590, 44, 28, GREEN, True)
    text(s, '增加归一化食物距离与相对八邻域障碍', 48, 348, 580, 65, 22)
    board(s, 684, 164, 210, True)
    text(s, '规则一致：允许进入当步腾出的旧尾格', 48, 450, 850, 38, 20, GRAY)
    notes(s, 'V1把棋盘压缩成十一维，分别描述三个相对动作的危险、四个朝向和四个食物方位。V2保留原特征，再加一个归一化曼哈顿距离和八个相对邻域障碍特征。图中浅绿色标出局部邻域。食物方位不互斥，斜向可以同时激活两项。环境还统一处理旧尾格，因为尾巴当步会移走。', 'A负责环境和V1基础，D后续完成V2及尾格占用集合更新修复；此处只解释设计，第8页报告效果。', 'docs/INTERFACE.md；docs/STATE_EXPERIMENT.md')

    s = slide('DQN 与统一训练框架', '经验回放与目标网络支持价值学习，三种算法共用运行流程')
    xs = [48, 274, 500, 726]
    for label, x in zip(['环境交互', '经验回放', '采样批次', 'Online 更新'], xs):
        node(s, label, x, 177, 186)
    for x in [242, 468, 694]:
        line(s, x, 209, x + 22, 209, GREEN, True)
    text(s, 'Target 网络提供下一状态价值', 48, 285, 860, 40, 24, GREEN, True)
    text(s, "y = r + γ(1 − terminated) max Q_target(s′, a′)", 48, 345, 864, 50, 24)
    text(s, 'epsilon-greedy 探索；截断仍 bootstrap\n统一训练、评估与模型加载，自动保存配置和日志', 48, 420, 864, 66, 21, GRAY)
    notes(s, 'DQN估计的是动作的长期价值，目标包含即时奖励和下一状态折扣价值。环境经历先写入回放池，再随机采样小批次更新在线网络，目标网络提供下一状态估值。只有真正终止才移除未来项，截断仍然bootstrap。探索用epsilon-greedy。我们让三算法共享训练、评估和模型恢复流程，避免复制三套代码带来额外差异。', '目标网络每1000次成功梯度更新同步，不按环境步计数。', 'algorithms/dqn.py；train.py；evaluate.py')

    s = slide('统一实验协议', '同组只改变研究变量，所有训练种子完整报告')
    table(s, [['项目', '设置'], ['对照训练', '每条件 3 个训练种子：42、43、44'],
              ['预算', '每模型 100,000 环境步'], ['网络与参数', '两层各 128；γ=0.99，学习率 0.001'],
              ['独立评估', '每模型 50 局，纯贪心、不更新网络'],
              ['核心指标', '食物数 Score；跨模型均值与总体 SD']], 48, 146, 864, 306, [185, 679], 21)
    text(s, '开发、复核、最终测试使用不同环境种子集', 48, 466, 864, 30, 20, GREEN)
    notes(s, '正式对照通常每个条件训练三个种子，每个模型十万环境步。网络使用两层一百二十八维隐藏层，学习率千分之一。各模型再用共同环境种子独立评估五十局，关闭探索和学习。主指标是食物数，误差是模型均分之间的总体标准差。五十局不能当成五十个训练种子。最后冻结配置，再扩展到五个训练种子和全新测试集。', '开发环境种子10000–10049，算法复核20000–20049，最终测试30000–30049。最终训练种子42–46。SD采用ddof=0，不是置信区间。', 'docs/EXPERIMENT_PROTOCOL.md；docs/FINAL_EXPERIMENT.md')

    s = slide('Double DQN：选择与评价分离', 'Online 选择动作，Target 评价该动作')
    text(s, 'DQN', 48, 169, 125, 40, 25, GREEN, True)
    node(s, 'Target 选最大', 210, 158, 240)
    node(s, 'Target 评价', 576, 158, 240)
    line(s, 464, 190, 560, 190, GREEN, True)
    text(s, 'Double', 48, 289, 150, 40, 25, GREEN, True)
    node(s, 'Online 选动作', 210, 278, 240)
    node(s, 'Target 评价', 576, 278, 240)
    line(s, 464, 310, 560, 310, GREEN, True)
    text(s, 'Q_target(s′, argmax Q_online(s′, a′))', 48, 384, 864, 45, 25)
    text(s, '只改变目标计算，不增加网络参数', 48, 452, 864, 34, 22, GRAY)
    notes(s, '标准DQN使用目标网络同时选择最大动作并评价该动作。估计有噪声时，max可能偏向取到高估值。Double把选择与评价分开：在线网络给出动作，目标网络评价这个动作。其余训练逻辑和终止约定不变，网络参数量不增加。这是缓解高估的设计动机，最终是否提高分数仍需实验判断。', '不保证消除全部偏差，本项目未测真实Q值偏差。Double多一次下一状态的Online前向，不能说计算量完全不变。', 'algorithms/double_dqn.py；tests/test_double_dqn.py')

    s = slide('Dueling DQN：状态价值与动作优势', '共享特征后分别估计 V 与 A，再聚合为三个动作的 Q 值')
    node(s, '共享特征层', 48, 234, 208, 72)
    node(s, 'Value：V(s)', 374, 160, 220, 66)
    node(s, 'Advantage：A(s,a)', 374, 316, 220, 66)
    node(s, '聚合\n三个动作 Q 值', 716, 226, 196, 96)
    line(s, 256, 270, 316, 270, GREEN)
    line(s, 316, 193, 316, 349, GREEN)
    line(s, 316, 193, 362, 193, GREEN, True)
    line(s, 316, 349, 362, 349, GREEN, True)
    line(s, 606, 193, 656, 193, GREEN)
    line(s, 606, 349, 656, 349, GREEN)
    line(s, 656, 193, 656, 349, GREEN)
    line(s, 656, 274, 704, 274, GREEN, True)
    text(s, 'Q(s,a) = V(s) + A(s,a) − mean A(s,a′)', 48, 420, 864, 44, 25)
    text(s, '沿用标准 DQN target，共享公共训练流程', 48, 476, 864, 27, 20, GRAY)
    notes(s, 'Dueling改变的是网络结构。共享层提取特征后，一路输出状态价值，一路输出三个动作的相对优势，再减去优势均值合成为Q值。减均值约束两部分的分解。输出仍是三个动作价值，所以公共训练评估接口保持一致。本项目这个版本沿用标准DQN目标，并不是Double和Dueling的组合。', '价值分解是表征设计，不等于已经证明更稳定或更高效。两种算法都做过数值和训练保存恢复验证。', 'algorithms/dueling_dqn.py；algorithms/networks.py')

    s = slide('V2 每局均分提高约 15.72%', '固定 DQN + sparse，仅改变状态表示')
    chart_anchor(s, 'CHART_STATE')
    text(s, '+15.72%', 628, 182, 284, 72, 44, GREEN, True)
    text(s, 'V1  19.17 ± 0.56\nV2  22.19 ± 0.65', 628, 285, 284, 90, 24)
    text(s, '每局得分改善\n未证明更稳定或寻食更高效', 628, 397, 284, 72, 20, GRAY)
    text(s, '误差棒：模型评估均分的跨训练种子总体 SD（3 seeds，ddof=0）', 48, 473, 850, 24, 16, GRAY)
    notes(s, '当前环境重新训练后，V1平均得分十九点一七，V2二十二点一九，提升约百分之十五点七。三个配对训练种子均提高。但波动没有降低，单位步数食物数也没提高。因此主要贡献是每局获得更多食物，不能理解成全面改善。', '两组同一尾格修复环境。V2同时新增距离和八邻域特征，增加1152参数，未拆分各自贡献。比例用未四舍五入均值计算。', 'docs/STATE_EXPERIMENT.md；results/state_experiments/state_v1_v2_20261018_134610_974148_b458c91f/comparison.json')

    s = slide('奖励塑形：更密集反馈未提高均分', '固定 V2 + DQN，距离系数 0.1，步惩罚 0.01')
    chart_anchor(s, 'CHART_REWARD', w=500)
    text(s, 'sparse', 602, 157, 310, 31, 23, GREEN, True)
    text(s, '食物 +10，死亡 −10', 602, 193, 310, 34, 20)
    text(s, 'distance', 602, 248, 310, 31, 23, GREEN, True)
    text(s, '额外奖励 0.1 × 距离减少量', 602, 284, 310, 58, 20)
    text(s, 'distance_step', 602, 354, 310, 31, 23, GREEN, True)
    text(s, 'distance 每动作再减 0.01', 602, 390, 310, 50, 20)
    text(s, '误差棒：跨训练种子总体 SD（ddof=0）；三组 SD：0.65 / 0.15 / 0.27', 48, 451, 864, 28, 16, GRAY)
    text(s, 'Return 216.16 > 211.87，但食物更少；跨奖励按 Score 比较', 48, 481, 864, 25, 17, CORAL)
    notes(s, '我实现了距离塑形和额外步惩罚，希望更密集的反馈帮助学习。但三个种子结果中，两种塑形均分都低于sparse。加步惩罚组的Return为二百一十六点一六，比sparse的二百一十一点八七更高，却吃得更少。这是因为奖励定义已经变化，所以跨奖励应该按Score比较，不能按回报或最高分选优。', '误差棒为跨训练模型均分的总体SD，3 seeds，ddof=0。距离比较同一个旧食物，碰撞时距离项为0；步惩罚含终止截断动作。启发式塑形，无策略不变保证。负结果只针对本次固定系数。', 'docs/REWARD_EXPERIMENT.md；results/reward_experiments/reward_v2_20261018_152348_243907_d0be64a1/comparison.json')

    s = slide('默认探索衰减在本次对照中均分最高', '固定 DQN + V2 + sparse，仅改变 epsilon 的衰减速度')
    chart_anchor(s, 'CHART_EXPLORATION', w=500)
    text(s, '快     0.9998\n默认  0.9999\n慢     0.99995', 602, 163, 310, 150, 25)
    text(s, 'epsilon：1.0 → 0.05\n按训练环境步更新', 602, 336, 310, 82, 22, GRAY)
    text(s, '训练得分早升 ≠ 最终贪心策略更好', 48, 449, 864, 31, 22, GREEN, True)
    text(s, 'Score：21.39 ± 0.96 / 22.19 ± 0.65 / 19.94 ± 0.34；误差为跨 seed 总体 SD', 48, 484, 864, 22, 16, GRAY)
    notes(s, '接下来只改变epsilon的衰减速度。快、默认、慢三组最终均分分别为二十一点三九、二十二点一九和十九点九四。默认方案最高，因此保留零点九九九九。快组训练曲线更早上升，却没有成为更好的最终贪心策略。', '同一epsilon-greedy的参数对照，不是三种探索算法。3训练seeds，SD采用ddof=0。没有证明更快收敛或普遍最优。', 'docs/EXPLORATION_EXPERIMENT.md')

    s = slide('综合比较与五种子最终验证', '三算法共同配置：V2 + sparse + 默认探索')
    table(s, [['算法', '开发均分 ± SD', '新种子复核均分 ± SD'],
              ['DQN', '22.19 ± 0.65', '21.45 ± 1.49'],
              ['Double DQN', '19.77 ± 0.74', '19.89 ± 1.01'],
              ['Dueling DQN', '21.01 ± 1.01', '20.83 ± 0.86'],
              ['Random', '0.04', '0.12']], 48, 139, 864, 200, [244, 290, 330], 20)
    text(s, '五训练种子最终确认', 48, 361, 864, 35, 23, GREEN, True)
    text(s, '开发集', 48, 414, 130, 28, 18, GRAY)
    text(s, '22.60 ± 1.19', 181, 407, 265, 47, 30, GREEN, True)
    text(s, '最终新测试', 494, 414, 150, 28, 18, GRAY)
    text(s, '20.76 ± 2.64', 648, 407, 264, 47, 30, GREEN, True)
    text(s, '冻结 DQN + V2 + sparse + 0.9999；最终 Random = 0.12', 48, 468, 864, 25, 17)
    text(s, '上表 3 seeds，下方 5 seeds；± 为跨模型均分总体 SD，两个复核/测试集不同', 48, 500, 810, 22, 16, GRAY)
    notes(s, '共同配置下DQN开发均分最高，换一组环境种子复核后排名相同，但不是每个训练种子都领先。前序配置围绕DQN选择，所以这里不能代表各算法分别调参后的上限。最后冻结DQN、V2、稀疏奖励和默认探索，扩展到五个训练种子，再用全新测试集确认。最终均分二十点七六、总体标准差二点六四。保留所有种子，也没有按测试最高分换模型，结果仍有明显波动。', '上表为3模型算法对照，下方为5模型最终确认，不能混算。开发种子10000–10049，复核20000–20049，最终30000–30049。五模型最终均分22.78/20.60/16.54/19.66/24.20，入口seed42预先固定。原三模型复用，新增45/46。', 'docs/ALGORITHM_EXPERIMENT.md；docs/FINAL_EXPERIMENT.md')

    s = slide('总结：改进需要实验验证')
    text(s, '统一环境与三种算法', 48, 139, 864, 45, 28, GREEN, True)
    text(s, '状态、奖励、探索对照，交互消融与五种子最终测试', 48, 194, 864, 58, 23)
    text(s, 'V2 改善每局得分', 48, 282, 864, 45, 28, GREEN, True)
    text(s, '密集奖励、探索调整与结构改动均需实际检验', 48, 337, 864, 58, 23)
    text(s, '局限：种子与预算有限，未证明显著性或普遍最优', 48, 423, 864, 36, 21, GRAY)
    text(s, 'A 环境与 V1    B DQN 与框架    C 改进算法    D V2 与实验分析', 48, 479, 825, 25, 17, GRAY)
    notes(s, '我们完成了统一环境、三种算法，以及状态、奖励、探索对照、交互消融和五种子最终测试。主要性能贡献来自V2状态表示，而密集奖励和结构改动并不保证提高得分。当前种子和预算仍有限，我们如实保留负结果与限制。谢谢大家。', '此版没有真实运行录像，不作现场Demo承诺。完整消融已完成，主讲不展开六格矩阵。', 'docs/D_WORK_SUMMARY.md；docs/STATE_REWARD_ABLATION.md；docs/FINAL_EXPERIMENT.md')

    base = BUILD / 'native_base.pptx'
    p.SaveAs(str(base), 24)
    print('Authored 12 native slides:', base, flush=True)
    (BUILD / 'geometry.json').write_text(json.dumps(GEOMETRY, ensure_ascii=False, indent=2), encoding='utf-8')
finally:
    p.Close()


NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def el(parent, name, attrib=None, value=None):
    prefix, local = name.split(':')
    e = ET.SubElement(parent, '{' + NS[prefix] + '}' + local, attrib or {})
    if value is not None:
        e.text = str(value)
    return e


def val(parent, name, v):
    return el(parent, name, {'val': str(v)})


def cached_ref(parent, kind, formula, values):
    ref = el(parent, 'c:' + kind + 'Ref')
    el(ref, 'c:f', value=formula)
    cache = el(ref, 'c:' + kind + 'Cache')
    if kind == 'num':
        el(cache, 'c:formatCode', value='0.00')
    val(cache, 'c:ptCount', len(values))
    for idx, v in enumerate(values):
        pt = el(cache, 'c:pt', {'idx': str(idx)})
        el(pt, 'c:v', value=v)


def chart_xml(cats, means, sds, colors):
    root = ET.Element('{' + NS['c'] + '}chartSpace')
    val(root, 'c:lang', 'zh-CN')
    chart = el(root, 'c:chart')
    val(chart, 'c:autoTitleDeleted', 1)
    plot = el(chart, 'c:plotArea')
    el(plot, 'c:layout')
    bar = el(plot, 'c:barChart')
    val(bar, 'c:barDir', 'col')
    val(bar, 'c:grouping', 'clustered')
    val(bar, 'c:varyColors', 1)
    ser = el(bar, 'c:ser')
    val(ser, 'c:idx', 0)
    val(ser, 'c:order', 0)
    el(el(ser, 'c:tx'), 'c:v', value='平均 Score')
    for i, col in enumerate(colors):
        point = el(ser, 'c:dPt')
        val(point, 'c:idx', i)
        sp = el(point, 'c:spPr')
        el(el(sp, 'a:solidFill'), 'a:srgbClr', {'val': col})
        el(el(sp, 'a:ln'), 'a:noFill')
    labels = el(ser, 'c:dLbls')
    el(labels, 'c:numFmt', {'formatCode': '0.00', 'sourceLinked': '0'})
    val(labels, 'c:dLblPos', 'outEnd')
    val(labels, 'c:showLegendKey', 0)
    val(labels, 'c:showVal', 1)
    val(labels, 'c:showCatName', 0)
    val(labels, 'c:showSerName', 0)
    val(labels, 'c:showPercent', 0)
    tx = el(labels, 'c:txPr')
    el(tx, 'a:bodyPr')
    el(tx, 'a:lstStyle')
    para = el(tx, 'a:p')
    el(el(para, 'a:pPr'), 'a:defRPr', {'sz': '1800'})
    err = el(ser, 'c:errBars')
    val(err, 'c:errDir', 'y')
    val(err, 'c:errBarType', 'both')
    val(err, 'c:errValType', 'cust')
    val(err, 'c:noEndCap', 0)
    for direction in ('plus', 'minus'):
        cached_ref(el(err, 'c:' + direction), 'num', f"'数据'!$C$2:$C${len(cats)+1}", sds)
    sp = el(err, 'c:spPr')
    el(el(el(sp, 'a:ln', {'w': '16000'}), 'a:solidFill'), 'a:srgbClr', {'val': INK})
    cached_ref(el(ser, 'c:cat'), 'str', f"'数据'!$A$2:$A${len(cats)+1}", cats)
    cached_ref(el(ser, 'c:val'), 'num', f"'数据'!$B$2:$B${len(cats)+1}", means)
    val(bar, 'c:gapWidth', 130)
    val(bar, 'c:axId', 100)
    val(bar, 'c:axId', 200)
    for axis_kind, ident, pos, other in [('catAx', 100, 'b', 200), ('valAx', 200, 'l', 100)]:
        ax = el(plot, 'c:' + axis_kind)
        val(ax, 'c:axId', ident)
        scaling = el(ax, 'c:scaling')
        val(scaling, 'c:orientation', 'minMax')
        if axis_kind == 'valAx':
            val(scaling, 'c:max', 30)
            val(scaling, 'c:min', 0)
        val(ax, 'c:delete', 0)
        val(ax, 'c:axPos', pos)
        if axis_kind == 'valAx':
            grid = el(ax, 'c:majorGridlines')
            sp = el(grid, 'c:spPr')
            el(el(el(sp, 'a:ln'), 'a:solidFill'), 'a:srgbClr', {'val': LINE})
            el(ax, 'c:numFmt', {'formatCode': '0', 'sourceLinked': '0'})
        val(ax, 'c:majorTickMark', 'none')
        val(ax, 'c:minorTickMark', 'none')
        val(ax, 'c:tickLblPos', 'nextTo')
        tx = el(ax, 'c:txPr')
        el(tx, 'a:bodyPr')
        el(tx, 'a:lstStyle')
        para = el(tx, 'a:p')
        rp = el(el(para, 'a:pPr'), 'a:defRPr', {'sz': '1700'})
        el(el(rp, 'a:solidFill'), 'a:srgbClr', {'val': INK})
        el(rp, 'a:latin', {'typeface': FONT})
        el(rp, 'a:ea', {'typeface': FONT})
        val(ax, 'c:crossAx', other)
        val(ax, 'c:crosses', 'autoZero')
        if axis_kind == 'catAx':
            val(ax, 'c:auto', 1)
            val(ax, 'c:lblAlgn', 'ctr')
            val(ax, 'c:lblOffset', 100)
        else:
            val(ax, 'c:crossBetween', 'between')
            val(ax, 'c:majorUnit', 10)
    val(chart, 'c:plotVisOnly', 1)
    val(chart, 'c:dispBlanksAs', 'gap')
    ext = el(root, 'c:externalData', {'{' + NS['r'] + '}id': 'rIdWorkbook'})
    val(ext, 'c:autoUpdate', 0)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


specs = [(8, 'CHART_STATE', ['V1', 'V2'], [19.17, 22.19], [.56, .65], ['81B9A2', GREEN]),
         (9, 'CHART_REWARD', ['sparse', 'distance', 'distance_step'], [22.19, 19.89, 21.31], [.65, .15, .27], [GREEN, CORAL, 'A5B7AE']),
         (10, 'CHART_EXPLORATION', ['快', '默认', '慢'], [21.39, 22.19, 19.94], [.96, .65, .34], ['A5B7AE', GREEN, CORAL])]
with zipfile.ZipFile(BUILD / 'native_base.pptx') as z:
    files = {name: z.read(name) for name in z.namelist()}
types = ET.fromstring(files['[Content_Types].xml'])
for chart_id, (page, name, cats, means, sds, colors) in enumerate(specs, 1):
    path = f'ppt/slides/slide{page}.xml'
    tree = ET.fromstring(files[path])
    sp_tree = tree.find('p:cSld/p:spTree', NS)
    anchor = next(sh for sh in sp_tree.findall('p:sp', NS)
                  if sh.find('p:nvSpPr/p:cNvPr', NS).get('name') == name)
    ident = anchor.find('p:nvSpPr/p:cNvPr', NS).get('id')
    transform = anchor.find('p:spPr/a:xfrm', NS)
    frame = ET.Element('{' + NS['p'] + '}graphicFrame')
    nv = el(frame, 'p:nvGraphicFramePr')
    el(nv, 'p:cNvPr', {'id': ident, 'name': 'EditableChart_' + str(page)})
    el(nv, 'p:cNvGraphicFramePr')
    el(nv, 'p:nvPr')
    trans = el(frame, 'p:xfrm')
    for child in transform:
        trans.append(child)
    graphic = el(frame, 'a:graphic')
    data = el(graphic, 'a:graphicData', {'uri': NS['c']})
    el(data, 'c:chart', {'{' + NS['r'] + '}id': 'rIdNativeChart'})
    index = list(sp_tree).index(anchor)
    sp_tree.remove(anchor)
    sp_tree.insert(index, frame)
    files[path] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    relpath = f'ppt/slides/_rels/slide{page}.xml.rels'
    rels = ET.fromstring(files[relpath])
    ET.SubElement(rels, '{' + PKG + '}Relationship', {'Id': 'rIdNativeChart',
                  'Type': NS['r'] + '/chart', 'Target': f'../charts/chart{chart_id}.xml'})
    files[relpath] = ET.tostring(rels, encoding='utf-8', xml_declaration=True)
    files[f'ppt/charts/chart{chart_id}.xml'] = chart_xml(cats, means, sds, colors)
    rels = ET.Element('{' + PKG + '}Relationships')
    ET.SubElement(rels, '{' + PKG + '}Relationship', {'Id': 'rIdWorkbook',
                  'Type': NS['r'] + '/package', 'Target': f'../embeddings/chart_data{chart_id}.xlsx'})
    files[f'ppt/charts/_rels/chart{chart_id}.xml.rels'] = ET.tostring(rels, encoding='utf-8', xml_declaration=True)
    wb = Workbook()
    ws = wb.active
    ws.title = '数据'
    ws.append(['方案', '平均 Score', '跨模型均分总体 SD'])
    for row in zip(cats, means, sds):
        ws.append(list(row))
    buf = BytesIO()
    wb.save(buf)
    files[f'ppt/embeddings/chart_data{chart_id}.xlsx'] = buf.getvalue()
    ET.SubElement(types, '{' + CT + '}Override', {'PartName': f'/ppt/charts/chart{chart_id}.xml',
                  'ContentType': 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml'})
if not any(e.get('Extension') == 'xlsx' for e in types):
    ET.SubElement(types, '{' + CT + '}Default', {'Extension': 'xlsx',
                  'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
ET.register_namespace('', CT)
files['[Content_Types].xml'] = ET.tostring(types, encoding='utf-8', xml_declaration=True)
final = OUT / 'Snake_RL_10min_editable.pptx'
if final.exists():
    raise FileExistsError('Refusing to overwrite existing deliverable: ' + str(final))
with zipfile.ZipFile(final, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, content in files.items():
        z.writestr(name, content)
print('Saved editable PPTX:', final, flush=True)
