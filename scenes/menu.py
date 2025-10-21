class Menu:
    def __init__(self, title, options):
        self.title = title
        self.options = options
        self.index = 0

    def move(self, delta):
        self.index = (self.index + delta) % len(self.options)

    def select(self):
        return self.options[self.index]
