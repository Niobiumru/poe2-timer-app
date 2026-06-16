import re

class LogParser:
    # Example: 2026/06/16 17:31:42 930764765 2caa1e77 [DEBUG Client 55380] Client-Safe Instance ID = 3502288093
    INSTANCE_RE = re.compile(r"Client-Safe Instance ID = (\d+)")
    
    # Example: 2026/06/16 17:31:42 930764765 2caa233f [DEBUG Client 55380] Generating level 79 area "MapIceCave" with seed 3623188112
    AREA_RE = re.compile(r"Generating level \d+ area \"([^\"]+)\"")

    @staticmethod
    def parse_line(line):
        instance_match = LogParser.INSTANCE_RE.search(line)
        if instance_match:
            return {"type": "instance", "value": instance_match.group(1)}
        
        area_match = LogParser.AREA_RE.search(line)
        if area_match:
            return {"type": "area", "value": area_match.group(1)}
        
        return None
