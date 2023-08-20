"""Simple functions to process OncoKB levels"""

def oncokb_level_to_html(level):
    if level == "1" or level == 1:
        html = '<div class="circle oncokb-level1">1</div>'
    elif level == "2" or level == 2:
        html = '<div class="circle oncokb-level2">2</div>'
    elif level == "3A":
        html = '<div class="circle oncokb-level3A">3A</div>'
    elif level == "3B":
        html = '<div class="circle oncokb-level3B">3B</div>'
    elif level == "4":
        html = '<div class="circle oncokb-level4">4</div>'
    elif level == "R1":
        html = '<div class="circle oncokb-levelR1">R1</div>'
    elif level == "R2":
        html = '<div class="circle oncokb-levelR2">R2</div>'
    elif level == "N1":
        html = '<div class="square oncokb-levelN1">N1</div>'
    elif level == "N2":
        html = '<div class="square oncokb-levelN2">N2</div>'
    elif level == "N3":
        html = '<div class="square oncokb-levelN3">N3</div>'
    else:
        raise RuntimeError("Unknown OncoKB level: '{0}'".format(level))
    return html

def oncokb_order(level):
    levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3']
    order = None
    for i in range(len(levels)):
        if str(level) == levels[i]:
            order = i
            break
    if order == None:
        raise RuntimeError("Unknown OncoKB level: {0}".format(level))
    return order
