# src/custom_formatter.py

import logging

class CustomFormatter(logging.Formatter):
    GREEN = '\033[92m'
    RESET = '\033[0m'
    
    def format(self, record):
        if record.msg in ["REMOVED CANCELLED ORDER", "ADDED NEW ORDER", "UPDATED PARTIAL FILL", "UPDATED FILL"]:
            record.msg = f"{self.GREEN}{record.msg}{self.RESET}"
        return super().format(record)
