import os
from PyPDF2 import PdfFileMerger

if __name__ == '__main__':
    # path = os.path.join(os.path.dirname(__file__), os.pardir, 'data/my_state_diagram_server.png')
    # draw_server_fsm(path)

    os.system('make clean')
    os.system('make report-server.pdf')
    pdfs = ['ОТЧЕТ ПО НИР_СЕТИ.pdf', 'report-server.pdf']
    merger = PdfFileMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write("result.pdf")
    merger.close()