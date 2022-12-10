
class ObjectiveBase:
    def setApp(self, app : 'DroneSimulator'):
        self.app = app
    def getObservation(self):
        return
    def getFitness(self) -> float:
        return
    def getIsDone(self) -> bool:
        return False
    def update(self):
        pass

