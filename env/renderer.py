"""pygame 渲染，与 ``snake_env.py`` 解耦。

只在 ``render_mode`` 非 None 时被 ``snake_env`` 惰性导入，所以训练
（默认 ``render_mode=None``）不会加载 pygame，见 ``docs/INTERFACE.md`` §9。

坐标系与棋盘一致：``row`` 向下、``col`` 向右，一个格子 ``CELL`` 像素。
"""
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np
import pygame
import pygame.surfarray

CELL = 40
BACKGROUND = (18, 18, 24)
GRID = (38, 38, 48)
SNAKE_HEAD = (130, 220, 130)
SNAKE_BODY = (60, 150, 80)
FOOD = (230, 80, 80)


class Renderer:
    """``board_size`` × ``board_size`` 棋盘的 pygame 渲染器。"""

    def __init__(self, board_size, mode):
        if mode not in ("human", "rgb_array"):
            raise ValueError(f"render_mode={mode!r}，应为 'human' 或 'rgb_array'")

        self.board_size = board_size
        self.mode = mode
        self.pixels = board_size * CELL

        pygame.init()
        if mode == "human":
            self.surface = pygame.display.set_mode((self.pixels, self.pixels))
        else:
            # 不建窗口：rgb_array 供录制视频用，不应弹出任何界面
            self.surface = pygame.Surface((self.pixels, self.pixels))

    def draw(self, body, food, score):
        """画一帧。

        human 模式刷屏并返回 None；rgb_array 模式返回 ``(H, W, 3)`` 的
        ``uint8`` 数组，符合 Gymnasium 的帧约定。
        """
        self.surface.fill(BACKGROUND)
        for i in range(self.board_size + 1):
            offset = i * CELL
            pygame.draw.line(self.surface, GRID, (offset, 0), (offset, self.pixels))
            pygame.draw.line(self.surface, GRID, (0, offset), (self.pixels, offset))

        self._fill(food, FOOD)
        head = body[0]
        for cell in body:
            self._fill(cell, SNAKE_HEAD if cell == head else SNAKE_BODY)

        if self.mode != "human":
            return np.transpose(pygame.surfarray.array3d(self.surface), (1, 0, 2))

        pygame.display.set_caption(f"Snake-RL    score={score}")
        pygame.display.flip()
        # 只维持窗口响应，不取走事件：事件队列由调用方的循环处理（见 play.py）
        pygame.event.pump()
        return None

    def _fill(self, cell, color):
        row, col = cell
        pygame.draw.rect(
            self.surface, color,
            pygame.Rect(col * CELL + 1, row * CELL + 1, CELL - 1, CELL - 1),
        )

    def close(self):
        pygame.quit()
