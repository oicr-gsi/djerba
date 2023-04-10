"""
List of functions to convert VIRUSBreakend information into json format.
"""

class data_builder:
  
  def build_virusbreakend(self):
          # read in small mutations; output rows for oncogenic mutations
          self.logger.debug("Building data for VIRUSBreakend table")
          virusbreakend_path = self.config[ini.DISCOVERED][ini.VIRUSBREAKEND_FILE]
          rows = []
          with open(os.path.join(self.input_dir, virusbreakend_path)) as data_file:
              for input_row in csv.DictReader(data_file, delimiter="\t"):
                  row = {
                      rc.GENUS: input_row[self.GENUS],
                      rc.SPECIES: input_row[self.SPECIES],
                      rc.COVERAGE: input_row[self.COVERAGE],
                      rc.LENGTH: input_row[self.LENGTH],
                      rc.MEANDEPTH: input_row[self.MEANDEPTH],
                      rc.INTEGRATION: input_row[self.INTEGRATION]
                  }
                  rows.append(row)
          self.logger.debug("Sorting and filtering VIRUSBreakend rows")
          num_viruses = len(rows)
          data = {
              rc.HAS_EXPRESSION_DATA: self.is_wgts,
              rc.TOTAL_VARIANTS: num_viruses
              rc.BODY: rows
          }
          return data 
