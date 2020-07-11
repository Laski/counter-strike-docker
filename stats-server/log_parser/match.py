class RoundInProgress:
    def __init__(self):
        self._events = []
        self._ended = False

    def has_ended(self):
        return self._ended

    def end(self):
        self._ended = True

    def record_event(self, event: 'Event'):
        self._events.append(event)

    def get_round_report(self):
        assert self._ended
        first_event = self._events[0]
        start_time = first_event.get_timestamp()
        last_event = self._events[-1]
        end_time = last_event.get_timestamp()
        return RoundReport(
            start_time=start_time,
            end_time=end_time,
            events=self._events
        )


class MatchInProgress:
    """
    A match is a sequence of rounds happening in a given map.
    This represents a match that hasn't ended yet.
    It's useful to construct MatchReport objects while parsing a log file.
    """

    def __init__(self):
        self._map_name = ''
        self._match_events = []
        self._ended_rounds = []
        self._ongoing_round = None
        self._ended = False

    def set_map_name(self, map_name):
        self._map_name = map_name

    def record_match_event(self, event):
        self._match_events.append(event)

    def record_round_event(self, event):
        self._ongoing_round.record_event(event)

    def start_new_round(self):
        if self._ongoing_round:
            assert self._ongoing_round.has_ended()
            round_report = self._ongoing_round.get_round_report()
            self._ended_rounds.append(round_report)
        self._ongoing_round = RoundInProgress()

    def end_current_round(self):
        self._ongoing_round.end()

    def impact_current_round_with(self, event: 'Event'):
        event.impact_round(self._ongoing_round)

    def has_ended(self):
        return self._ended

    def end(self):
        self._ended = True

    def get_match_report(self):
        assert self._ended
        first_event = self._match_events[0]
        start_time = first_event.get_timestamp()
        last_event = self._match_events[-1]
        end_time = last_event.get_timestamp()

        report = MatchReport(
            start_time=start_time,
            end_time=end_time,
            map_name=self._map_name,
            rounds=self._ended_rounds
        )
        return report


class MatchReport:
    """
    An inmutable representation of an ended match.
    A match is a sequence of rounds happening in a given map.
    Every log file contains one match.
    """

    def __init__(self, start_time, end_time, map_name, rounds):
        self._start_time = start_time
        self._end_time = end_time
        self._map_name = map_name
        self._rounds = tuple(rounds)  # make inmutable

    def get_rounds(self):
        return self._rounds

    def get_first_attack(self):
        for event in self._all_round_events():
            if event.is_attack():
                return event
        raise Exception("There's no blood in this game")

    def get_first_kill(self):
        for event in self._all_round_events():
            if event.is_kill():
                return event
        raise Exception("There's no kills in this game")

    def get_map_name(self):
        return self._map_name

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def _all_round_events(self):
        return (event for round in self.get_rounds() for event in round.get_events())


class RoundReport(object):
    def __init__(self, start_time, end_time, events):
        self._start_time = start_time
        self._end_time = end_time
        self._events = tuple(events)  # make inmutable

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_events(self):
        return self._events
