#!/usr/bin/env python3

import argparse
import pysrt


def parse_srt_file(file_path):
    subs = pysrt.open(file_path, encoding='utf-8')
    content = ""

    for sub in subs:
        content += sub.text.replace('<i>', '').replace('</i>', '') + '\n'

    return content.strip()


def write_readable_text(content, output_file_path=None):
    if output_file_path:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Readable text has been written to: {output_file_path}")
    else:
        print(content)


def main():
    parser = argparse.ArgumentParser(
        description='Convert SRT subtitle file to readable text.')
    parser.add_argument('input_file', help='Path to the input SRT file.')
    parser.add_argument(
        '-o',
        '--output',
        help=
        'Path to the output text file. If not provided, the content will be printed to the screen.',
        default=None)
    args = parser.parse_args()

    parsed_content = parse_srt_file(args.input_file)
    write_readable_text(parsed_content, args.output)


if __name__ == '__main__':
    main()
