from math import floor

class TimeCodedWord:

    def __init__(self, word, time):
        self.word = word
        self.time = int(floor(time))

    def __str__(self):
        return 'word: ' + str(self.word) + ', ' + 'time: ' + str(self.time)
