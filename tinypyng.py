import os, requests, json, time, argparse

SHRINK_URL = 'https://tinypng.com/web/shrink'
HEADERS = {
    'user-agent': 'Mozilla/5.0',
    'content-type': 'image/png'
}

class TinyPng:
    def __init__(self, log=True):
        self.png = None
        self.output_folder = None
        self.log_enabled = log
        self.is_recursive = False
        self.raw_data = None
        self.api = None
        self.url = None

    def log(self, text):
        if self.log_enabled:
            print(text)

    def rename(self, url):
        *perfix, ext = os.path.basename(self.png).split('.')
        return f'{url}/{".".join(perfix)}_compressed.{ext}'

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
        
        with open(os.path.join(dir_name, base_name), 'wb') as png:
            raw_data = requests.get(self.url).content
            png.write(raw_data)
    
    def compress(self):
        if not self.raw_data:
            self.raw_data = open(self.png, 'rb').read()
        
        self.log(f'[UPLOAD] {os.path.basename(self.png)}')
        response = requests.post(
            SHRINK_URL,
            headers=HEADERS,
            data=self.raw_data
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
            while self.api['ratio']:
                self.raw_data = requests.get(self.api['output']).content
                self.compress()
                self.save()
        
        except KeyboardInterrupt:
            self.log(f'[ERROR] Recursion Interrupted!')
        
        ratio = round((before - self.api['after']) * 100 / before, 2)
        self.log(f'[FINAL] Compression: {before}'
                 f' => {self.api["after"]} = {ratio}%')

        self.save()

    def batch_compress(self, file_list):
        for file in file_list:
            self.png = file
            self.log('[BATCH] Processing ' + os.path.basename(file))
            self.compress()

    def batch_recursive(self, file_list):
        for file in file_list:
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

    if inpt[-3:] == 'txt':
        files = [i for i in open(inpt).read().split('\n') if os.path.exists(i)]
        if not files:
            return print('Nothing found or no valid paths in', os.path.basename(inpt))
        return files
    
    return [inpt] if inpt[-3:] in 'pngjpg' else None
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Argument parser for tinypy')
    parser._action_groups.pop()

    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-p', '--path', type=str, help='PNG or JPG file, Directory of PNGs, txt file of paths', required=True, default=".")
    optional.add_argument('-r', '--recursive', help='Recursively compress the photo to the maximum possible limit', action='store_true')
    optional.add_argument('-o', '--output', type=str, default=None, help='Custom folder to store compressed pictures')

    args = parser.parse_args()

    tinypng = TinyPng()
    tinypng.is_recursive = args.recursive
    tinypng.output_folder = args.output

    files = decide_type(args.path)

    if not files:
        exit(0)

    if tinypng.recursive:
        tinypng.batch_recursive(files)
    else:
        tinypng.batch_compress(files)