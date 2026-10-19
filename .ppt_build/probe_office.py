from pathlib import Path
import win32com.client

root = Path(__file__).resolve().parent
app = win32com.client.DispatchEx('PowerPoint.Application')
print('Office COM', app.Version, flush=True)
p = app.Presentations.Add(0)
try:
    p.PageSetup.SlideWidth = 960
    p.PageSetup.SlideHeight = 540
    s = p.Slides.Add(1, 12)
    t = s.Shapes.AddTextbox(1, 40, 40, 600, 90)
    t.TextFrame.TextRange.Text = '中文可编辑测试'
    t.TextFrame.TextRange.Font.Name = 'Microsoft YaHei'
    t.TextFrame.TextRange.Font.Size = 30
    try:
        c = s.Shapes.AddChart(51, 40, 150, 600, 280)
        print('Chart object:', c.HasChart, flush=True)
        print('ChartData available:', c.Chart.ChartData, flush=True)
    except Exception as e:
        print('Chart test:', repr(e), flush=True)
    try:
        s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = '汇报人 A；20 秒。演讲备注测试。'
        print('Notes okay', flush=True)
    except Exception as e:
        print('Notes test:', repr(e), flush=True)
    p.SaveAs(str(root / 'probe.pptx'), 24)
    print('PPTX saved', flush=True)
    s.Export(str(root / 'probe.png'), 'PNG', 1280, 720)
    print('PNG exported', flush=True)
    p.SaveAs(str(root / 'probe.pdf'), 32)
    print('PDF exported', flush=True)
finally:
    p.Close()
