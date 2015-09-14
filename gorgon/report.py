import json
from time import time
from collections import defaultdict

HTML_TEMPLATE = '''
<html>
  <head>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {{packages:["corechart"]}});
      google.setOnLoadCallback(drawChart);
      function drawChart() {{
        var data = google.visualization.arrayToDataTable([
          [{titles}],
          {data}
        ]);

        var options = {{
            title: 'Gorgon',
            //vAxes:[{{}}, {{}}],
            //series: [{{targetAxisIndex:0}}, {{targetAxisIndex:1}}]
        }};

        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }}
    </script>
  </head>
  <body>
    <div id="chart_div" style="width: 1500px; height: 800px;"></div>
  </body>
</html>

'''


def average(data):
    total_sum = 0
    total_len = 0
    for d in data:
        total_sum += d
        total_len += 1

    return total_sum // total_len


class GorgonReport(object):

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.calls = []
        self.full_report = []

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

    TINY_FORMAT = '{ms: 3,}ms'
    SMALL_FORMAT = '{seconds: 2,}s {ms: 3,}ms'
    MEDIUM_FORMAT = '{minutes: 2,}m {seconds: 2,}s {ms: 3,}ms'
    BIG_FORMAT = '{hours}h {minutes: 2,}m {seconds: 2,}s {ms: 3,}ms'

    def append(self, report):
        ''' Append a report to this one '''
        self.calls.extend(report.calls)

    def append_cluster(self, report_line):
        report = json.loads(report_line)
        self.calls.extend(report)

    @property
    def formatted_total_time(self):
        return self.formatted_time(self.total_time)

    def formatted_time(self, unformatted_time):
        ms = int((unformatted_time % 1) * 1000)
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

        if average == 0:
            TEMPLATE = ('{number: 10}  Inf! ops/sec. Avg time: {avg} '
                        'Max: {maximum} Min: {minimum}')
            opssec = None
        else:
            TEMPLATE = ('{number: 10}  {opssec: 7,} ops/sec. '
                        'Avg time: {avg} '
                        'Max: {maximum} Min: {minimum}')
            total_time = end_time - start_time
            opssec = int(number / total_time)

        report = TEMPLATE.format(number=number,
                                 opssec=opssec,
                                 avg=self.formatted_time(average),
                                 maximum=self.formatted_time(maximum),
                                 minimum=self.formatted_time(minimum))
        return report

    def _get_id_calls_start_end(self):
        id_calls = defaultdict(dict)
        start_time = self.calls[0]['start_time']
        end_time = 0
        for item in self.calls:
            id_calls[str(item['call_id'])].update(item)
            if 'start_time' in item:
                start_time = min(start_time, item['start_time'])
            if 'end_time' in item:
                end_time = max(start_time, item['end_time'])

        for item in id_calls.values():
            item['total_time'] = item['end_time'] - item['start_time']

        return id_calls, start_time, end_time

    def _group_by(self, id_calls, group):
        group_calls = defaultdict(list)

        for call_id, item in id_calls.items():
            group_calls[item[group]].append(item)

        return group_calls

    def small_report(self):
        self.full_report = []

        RESULT_HEADER = 'Result'
        len_result = len(RESULT_HEADER)
        id_calls, start_time, end_time = self._get_id_calls_start_end()
        self.start_time = start_time
        self.end_time = end_time
        for call_id, item in id_calls.items():
            generator = (k for k in item.keys()
                         if k == 'result' or k.startswith('time_'))
            for key in generator:
                len_result = max(len_result, len(str(item[key])))

        REPORT_TEMPLATE = '{{name:>{}}} {{report}}'.format(len_result)

        group_calls = defaultdict(list)
        total_times = [item['total_time'] for item in id_calls.values()]
        group_calls = self._group_by(id_calls, 'result')

        header = REPORT_TEMPLATE.format(
            name='Result',
            report=self.times_report(total_times,
                                     self.start_time,
                                     self.end_time)
        )
        self.full_report.append(header)

        for group, calls in group_calls.items():
            start_time = min(item['start_time'] for item in calls)
            end_time = max(item['end_time'] for item in calls)
            times = [item['total_time'] for item in calls]

            row = (REPORT_TEMPLATE.format(name=group,
                                          report=self.times_report(times,
                                                                   start_time,
                                                                   end_time)))
            self.full_report.append(row)

            # append the subcalls

            # Check subcalls first
            subcalls = {key.lstrip('time_') for key in item.keys()
                          if key.startswith('time_')
                        for item in calls}
            for subcall in subcalls:
                key_name = 'time_{}'.format(subcall)
                times = [item[key_name] for item in calls if key_name in item]
                report = self.times_report(times, start_time, end_time)
                name = '{}<'.format(subcall)
                row = " " + REPORT_TEMPLATE.format(name=name, report=report)
                self.full_report.append(row)

        self.num_operations = len(id_calls)

        # Not sure if we should show the start/end time
        # Maybe useful in long tests
        # print('Start time', self.formatted_start_time)
        # print('End time', self.formatted_end_time)

        result = ['Total time: {}'.format(self.formatted_total_time)]
        result.extend(self.full_report)
        return '\n'.join(result)

    def start_call(self, uuid):
        info = {
            'call_id': uuid,
            'start_time': time(),
        }
        self.calls.append(info)

    def end_call(self, uuid, result):
        info = {
            'call_id': uuid,
            'end_time': time(),
            'result': result
        }
        self.calls.append(info)

    def context_call(self, uuid, name, int_time):
        info = {
            'call_id': uuid,
            'time_{}'.format(name): int_time,
        }
        self.calls.append(info)

    def html_graph_report(self):
        '''
        Generate data to be printed as a graph
        '''
        # Group the data by second
        id_calls, start_time, end_time = self._get_id_calls_start_end()
        # First by result
        group_calls = self._group_by(id_calls, 'result')

        # Group end calls in the same second
        by_second = defaultdict(lambda: defaultdict(list))
        for title, results in group_calls.items():
            for result in results:
                timestamp = int(result['end_time'])
                by_second[title][timestamp].append(result)

        # Get info per second
        by_second_info = defaultdict(lambda: defaultdict(list))
        for title, times in by_second.items():
            for timestamp, data in times.items():
                # in ms
                this_second_times = [int(d['total_time'] * 1000)
                                     for d in data]
                info = {
                    'operations': len(data),
                    'average': average(this_second_times),
                    'maximum': max(this_second_times),
                    'minimum': min(this_second_times),
                }
                by_second_info[timestamp][title] = info

        titles = list(by_second.keys())

        formatted_data = []
        for timestamp, tinfo in sorted(by_second_info.items(),
                                       key=lambda x: x[0]):
            data = [int(timestamp - start_time)]
            formatted_ops = [tinfo.get(title, {}).get('operations', 0)
                             for title in titles]
            data += formatted_ops
            formatted_data.append(data)

        page = self.google_chart(titles, formatted_data)
        return page

    def cluster_report(self):
        ''' Return the calls in JSON format to be transmitted '''
        id_calls, start_time, end_time = self._get_id_calls_start_end()
        return json.dumps([v for v in id_calls.values()])

    def google_chart(self, titles, data):
        all_titles = ['Timestamp'] + titles
        TITLE_TMPL = ', '.join('"{}"'.format(t.replace('"', "'"))
                                             for t in all_titles)
        LINE_TMPL = ', '.join('{}' for t in all_titles)
        LINE_FORMAT = "[" + LINE_TMPL + "]"
        format_data = []
        for line in data:
            format_data.append(LINE_FORMAT.format(*line))

        # Remove the last comma
        format_data[-1] = format_data[-1].rstrip(',')

        page = HTML_TEMPLATE.format(data=',\n          '.join(format_data),
                                    titles=TITLE_TMPL)

        return page

    def context_ready(self, uuid):
        return Context(self, uuid)


class GorgonMeasurement(object):

    def __init__(self, name, context):
        self.name = name
        self.context = context

    def __enter__(self):
        self.start_time = time()

    def __exit__(self, type, value, traceback):
        self.end_time = time()

        # Set a new call for the
        total_time = self.end_time - self.start_time
        self.context.report.context_call(self.context.uuid, self.name,
                                         total_time)


class Context(object):

    def __init__(self, report, uuid):
        self.report = report
        self.uuid = uuid

    def measurement(self, name):
        '''
        This context allows to do:
            with gorgon.measurement('name'):
                subcall

        that will be measured
        '''
        return GorgonMeasurement(name, self)
