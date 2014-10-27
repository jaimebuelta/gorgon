from time import time
from collections import deque, defaultdict


class GorgonReport(object):

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.calls = deque()
        self.full_report = None

    def end(self):
        # Create the report
        self.create_report()

    @property
    def total_time(self):
        return self.end_time - self.start_time

    @property
    def formatted_start_time(self):
        return self.start_time

    @property
    def formatted_end_time(self):
        return self.end_time

    TINY_FORMAT = '{ms}ms'
    SMALL_FORMAT = '{seconds}s {ms}ms'
    MEDIUM_FORMAT = '{minutes}m {seconds}s {ms}ms'
    BIG_FORMAT = '{hours}h {minutes}m {seconds}s {ms}ms'

    @property
    def formatted_total_time(self):
        return self.formatted_time(self.total_time)

    def formatted_time(self, unformatted_time):
        ms = int((unformatted_time % 1) * 100)
        total_sec = int(unformatted_time)
        total_minutes = (total_sec // 60)
        hours = (total_minutes // 60)
        seconds = total_sec % 60
        minutes = total_minutes % 60
        if hours and minutes:
            template = self.BIG_FORMAT
        elif minutes:
            template = self.MEDIUM_FORMAT
        elif seconds:
            template = self.SMALL_FORMAT
        else:
            template = self.TINY_FORMAT

        formatted_msg = template.format(hours=hours,
                                        minutes=minutes,
                                        seconds=seconds,
                                        ms=ms)

        return formatted_msg

    def times_report(self, times, start_time, end_time):
        ''' Get a list of times and return a string with the report '''

        number = len(times)
        average = sum(times) / number
        maximum = max(times)
        minimum = min(times)

        reqsec = int(number / (end_time - start_time))

        TEMPLATE = ('{number: 10}.  {reqsec: 7,} req/sec. Avg time: {avg} '
                    'Max: {maximum} Min: {minimum}')
        report = TEMPLATE.format(number=number,
                                 reqsec=reqsec,
                                 avg=self.formatted_time(average),
                                 maximum=self.formatted_time(maximum),
                                 minimum=self.formatted_time(minimum))
        return report

    def create_report(self):
        print('Creating report')
        id_calls = defaultdict(dict)
        for item in self.calls:
            id_calls[item['call_id']].update(item)

        self.start_time = min(item['start_time'] for item in id_calls.values())
        self.end_time = max(item['end_time'] for item in id_calls.values())

        REPORT_TEMPLATE = '{name:20} {report}'

        group_calls = defaultdict(list)
        total_times = deque()
        for call_id, item in id_calls.items():
            item['total_time'] = item['end_time'] - item['start_time']
            total_times.append(item['total_time'])
            group_calls[item['group']].append(item)

        print(REPORT_TEMPLATE.format(name='Total',
                                     report=self.times_report(total_times,
                                                              self.start_time,
                                                              self.end_time)))

        for group, calls in group_calls.items():
            start_time = min(item['start_time'] for item in calls)
            end_time = max(item['end_time'] for item in calls)
            times = [item['total_time'] for item in calls]

            print(REPORT_TEMPLATE.format(name=group,
                                         report=self.times_report(times,
                                                                  start_time,
                                                                  end_time)))

    def print_report(self):
        print('Start time', self.formatted_start_time)
        print('End time', self.formatted_end_time)
        print('Total time', self.formatted_total_time)

    def start_call(self, uuid, group):
        info = {
            'call_id': uuid,
            'group': group,
            'start_time': time(),
        }
        self.calls.append(info)

    def end_call(self, uuid):
        info = {
            'call_id': uuid,
            'end_time': time(),
        }
        self.calls.append(info)
