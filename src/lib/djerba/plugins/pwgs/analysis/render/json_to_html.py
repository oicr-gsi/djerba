"""collection of functions for rendering Djerba content in Mako"""

import re
from markdown import markdown
from time import strftime
from string import Template
import djerba.plugins.pwgs.constants as constants

class html_builder:
    def k_comma_format(self,value):
        value_formatted = f'{value:,}'
        return(value_formatted)
        
    def section_cells_begin(self, section_title, main_or_supp):
        # begin a cell structure with title in left-hand cell, body in right-hand cell
        permitted = ['main', 'supp']
        if main_or_supp not in permitted:
            msg = "Section type argument '{0}' not in {1}".format(main_or_supp, permitted)
            self.logger.error(msg)
            raise RuntimeError(msg)
        template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'
        cell = template.format(main_or_supp,section_title)
        return cell

    def section_cells_end(self):
        # closes <div class="twocell... and <div class="twooftwocell...
        return "</div></div>\n"

