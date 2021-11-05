import os, requests, json, time, argparse
from randagent import generate_useragent

SHRINK_URL = 'https://tinypng.com/web/shrink'
HEADERS = {
    'user-agent': 'Mozilla/5.0',
    'content-type': 'image/png'
}

class upload_in_chunks:
    def __init__(self, raw_data, ext, chunksize=1 << 13):
        self.filename = f'tinypyng_temp.{ext}'
        open(self.filename, 'wb').write(raw_data)
        
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(self.filename)
        self.readsofar = 0

    def __iter__(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    print()
                    break
                self.readsofar += len(data)

                percent = int((self.readsofar * 50 / self.totalsize))
                size_type = 1 << 20
                if self.totalsize < size_type:
                    size_type = 1 << 10
                r_size = self.totalsize / size_type
                d_size = self.readsofar / size_type
                pgbar = '[PROGRESS] [{}{}] '.format(
                    '█' * percent,
                    ' ' * (50 - percent)) + '[{0:.2f}/{1:.2f} {2}]'.format(d_size, r_size, ['KB', 'MB'][size_type == 1 << 20])
                print(f'\r{pgbar}'.format(percent=percent), end='\r')
                yield data
        
        os.remove(self.filename)

    def __len__(self):
        return self.totalsize

def percent(total, current):
    return round((total - current) * 100 / total, 2)

def get_ext(_file):
    *_, ext = os.path.basename(_file).split('.')
    return ext

class TinyPyng:
    def __init__(self, log=True):
        self.png = None
        self.output_folder = None
        self.log_enabled = log
        self.is_recursive = False
        self.raw_data = None
        self.api = None
        self.url = None
        self.overwrite = False
        self.max = 50

    def correct_max(self):
        if self.max < 0 or self.max > 100:
            self.max = 100

    def log(self, text):
        if self.log_enabled:
            print(text)

    def rename(self, url):
        *perfix, ext = os.path.basename(self.png).split('.')
        postfix = '' if self.overwrite else '_compressed'
        return f'{url}/{".".join(perfix)}{postfix}.{ext}'

    def prettify(self, response):
        dct = json.loads(response)

        if 'error' in dct:
            return None

        output = dct['output']
        
        return {
            'before': dct['input']['size'],
            'after':  output['size'],
            'ratio':  round(100 - output['ratio'] * 100, 2),
            'output': self.rename(output['url'])
        }

    def save(self):
        self.url = self.api['output']
        
        dir_name = os.path.dirname(self.png)

        if self.output_folder:
            dir_name = os.path.dirname(
                os.path.join(self.output_folder, '')
            )

        base_name = self.url.split('/')[-1]
        
        raw_data = requests.get(
            self.url,
            headers={'user-agent': generate_useragent()}
        ).content
        
        with open(os.path.join(dir_name, base_name), 'wb') as png:
            png.write(raw_data)

    def compress(self):
        if not self.raw_data:
            self.raw_data = open(self.png, 'rb').read()
        
        self.log(f"[RECURSIVE {['OFF', 'ON'][self.is_recursive]}]")
        self.log(f'[UPLOAD] {os.path.basename(self.png)}')
        
        HEADERS['user-agent'] = generate_useragent()
        
        response = requests.post(
            SHRINK_URL,
            headers=HEADERS,
            data=upload_in_chunks(self.raw_data, get_ext(self.png))
        )

        self.api = self.prettify(response.text)

        if not self.api:
            self.log('[ERROR] Too many requests, Re-trying...')
            time.sleep(3)
            return self.compress()
        
        self.log('[DONE] Compression: {0} => {1} = {2}%'.format(*self.api.values()))

        self.save()
    
    def recursive(self):
        """
        Compress the png recursively till max_compression
        """
        self.is_recursive = True
        self.compress()
        
        before = self.api['before']

        try:
            while self.api['ratio'] and percent(before, self.api['after']) < self.max:
                self.raw_data = requests.get(
                    self.api['output'],
                    headers={'user-agent': generate_useragent()}
                ).content
                self.compress()
                self.save()
        
        except KeyboardInterrupt:
            self.log(f'[ERROR] Recursion Interrupted!')
        
        ratio = percent(before, self.api['after'])
        self.log(f'[FINAL] Compression: {before}'
                 f' => {self.api["after"]} = {ratio}%')

        self.save()

    def batch_compress(self, file_list):
        output_folder = self.output_folder
        for file in file_list:
            self.__init__()
            self.output_folder = output_folder
            self.png = file
            self.log('[BATCH] Processing ' + os.path.basename(file))
            self.compress()

    def batch_recursive(self, file_list):
        output_folder = self.output_folder
        for file in file_list:
            self.__init__()
            self.output_folder = output_folder
            self.png = file
            self.log('[BATCH] Processing ' + os.path.basename(file))
            self.recursive()

def decide_type(inpt):
    if not os.path.exists(inpt):
        print(inpt, 'does not exists!')
        return None

    if os.path.isdir(inpt):
        files = [os.path.join(inpt, i) for i in os.listdir(inpt) if i[-3:] in 'pngjpg']
        return print('Nothing found in', inpt) if not files else files

    if inpt[-3:].lower() == 'txt':
        files = [i for i in open(inpt).read().split('\n') if os.path.exists(i)]
        if not files:
            return print('Nothing found or no valid paths in', os.path.basename(inpt))
        return files

    return [inpt] if inpt[-3:].lower() in 'pngjpg' else print('Unsupported file format!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Argument parser for tinypy')
    parser._action_groups.pop()

    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-p', '--path', type=str, help='PNG or JPG file, Directory of PNGs, txt file of paths', required=True, default=".")
    optional.add_argument('-r', '--recursive', help='Recursively compress the photo to the maximum possible limit', action='store_true')
    optional.add_argument('-o', '--output', type=str, default=None, help='Custom folder to store compressed pictures')
    optional.add_argument('-m', '--max', type=int, default=50, help='Maximum compression ratio -- Default is 50 --')
    optional.add_argument('-ow', '--overwrite', help='Overwrite input PNG', action='store_true')

    args = parser.parse_args()

    tinypng = TinyPyng()
    tinypng.is_recursive = args.recursive
    tinypng.output_folder = args.output
    tinypng.max = args.max
    tinypng.overwrite = args.overwrite

    files = decide_type(args.path)

    if not files:
        exit(0)
    
    if len(files) == 1:
        tinypng.png = files[0]
        [tinypng.compress, tinypng.recursive][args.recursive]()
    else:
        [tinypng.batch_compress, tinypng.batch_recursive][args.recursive](files)