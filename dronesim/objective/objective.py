
class ObjectiveBase:
    def set_app(self, app: 'DroneSimulator'):
        self.app = app

    def get_observation(self):
        return

    def get_fitness(self) -> float:
        return

    def get_is_done(self) -> bool:
        return False

    def update(self):
        pass
