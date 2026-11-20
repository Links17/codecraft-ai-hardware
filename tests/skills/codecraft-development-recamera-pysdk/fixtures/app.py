from kit.app import App

class FixtureApp(App):
    owns_loop = True

    def run(self):
        return None

raise AssertionError("Offline validation must not execute application code")
