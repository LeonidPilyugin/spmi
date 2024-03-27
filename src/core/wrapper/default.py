class Wrapper(Cover.Wrapper):
    def __init__(self, command: str, logfile: Path, logger: Logger):
        self.command = command
        self.logfile = logfile
        self.logger = logger
    
    def on_therm(self):
        pass

    def run(self):
        with open(self.logfile, "w") as f:
            p = subprocess.Popen(self.command, shell=True, stdin=f, stdout=f)
            p.wait()



