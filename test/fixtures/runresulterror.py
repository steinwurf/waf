

class RunResultError(Exception):
    """Exception for TestDirctory::run"""
    def __init__(self, runresult):
        super(RunResultError, self).__init__(str(runresult))
        self.runresult = runresult
