import re
import time

BASE_DIR = ''

NCPU = 1

CONTENT_TYPES = {
    None:'text/plain',
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.swf': 'application/x-shockwave-flash'
}

DAY_NAME = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

MONTH_NAME = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def get_ncpu():
    global NCPU
    return NCPU


def get_base_dir():
    global BASE_DIR
    return BASE_DIR


def change_base_dir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir


def http_parser(request):
    # pattern = '(GET|HEAD)\s+(([/\w\s\.$-]+)(\.([a-zA-Z\s]+))?)(\?([\w=&-]+))?\s+HTTP/([.0-9]+)'
    pattern = '(GET|HEAD)\s+([/\w\s\.$-]+)(\?([\w=&-]+))?\s+HTTP/([.0-9]+)'
    result = re.findall(pattern, request)
    if result.__len__() != 1:
        return None, None, None
    method = result[0][0]
    path = result[0][1]
    http_version = result[0][4]
    return method, path, http_version


def read_file(path):
    if '..' in path:
        raise IOError
    path_ = get_base_dir() + path
    file = open(path_, 'r')
    data = file.read()
    length = data.__len__()
    return data, length


def make_response_header(data_type, length, http_version):
    http_h = 'HTTP/{} 200 OK'.format(http_version)
    content_length = 'Content-Length: {}'.format(length)
    date = 'Date:{}'.format(get_date())
    setver = 'Server: {}'.format("DVVServer 0.1")
    type_ = 'Content-Type: {}'.format(data_type)
    connection = 'Connection: {}'.format("close")
    end_of_header = '\r\n'
    header = '\r\n'.join([http_h, content_length, date, setver, type_, connection, end_of_header])
    return header


def make_40X_resopnse_header(response):
    header = 'HTTP/1.1 {2}\r\nDate:{0}\r\nServer: {1}\r\n'.format(get_date(), "DVVServer 0.1", response)
    return header


def determinate_content_type(path):
    pattern = r'\.([\w]{1,5})$'
    type_ = re.search(pattern, path)
    if type_:
        try:
            return True, CONTENT_TYPES[type_.group(0)]
        except KeyError:
            return True, CONTENT_TYPES[None]
    else:
        return False, CONTENT_TYPES['.html']


def get_date():
    timestamp = time.time()
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    _time = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        DAY_NAME[wd],
        day, MONTH_NAME[month], year,
        hh, mm, ss)
    return _time