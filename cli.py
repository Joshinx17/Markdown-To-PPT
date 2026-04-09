"""
Command-line interface for the MD -> PPTX pipeline.

Usage:
  python cli.py --input report.md --output output/report.pptx
  python cli.py --input report.md --output output/report.pptx --slides 14
  python cli.py --input report.md --output output/report.pptx --api-key YOUR_KEY
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')
INPUT_DIR = Path(__file__).parent / 'input'


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
        datefmt='%H:%M:%S',
    )


@click.command()
@click.option(
    '--input', '-i', 'input_path',
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help='Path to the input Markdown (.md) file. If omitted, the newest .md file in input/ is used.',
)
@click.option(
    '--output', '-o', 'output_path',
    default=None,
    help='Path for the output .pptx file. Defaults to <input_name>.pptx.',
)
@click.option(
    '--slides', '-s',
    default=12,
    show_default=True,
    type=click.IntRange(10, 15),
    help='Target slide count (10-15).',
)
@click.option(
    '--min-slides',
    default=10,
    show_default=True,
    type=click.IntRange(5, 15),
    help='Minimum slide count.',
)
@click.option(
    '--max-slides',
    default=15,
    show_default=True,
    type=click.IntRange(10, 20),
    help='Maximum slide count.',
)
@click.option(
    '--api-key', '-k',
    default=None,
    envvar='GEMINI_API_KEY',
    help='Google Gemini API key. Falls back to GEMINI_API_KEY env var.',
)
@click.option(
    '--model',
    default='gemini-2.0-flash',
    show_default=True,
    help='Gemini model name.',
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    default=False,
    help='Enable debug logging.',
)
def main(
    input_path: str | None,
    output_path: str | None,
    slides: int,
    min_slides: int,
    max_slides: int,
    api_key: str | None,
    model: str,
    verbose: bool,
) -> None:
    """Convert Markdown into a polished PowerPoint deck."""
    _setup_logging(verbose)
    INPUT_DIR.mkdir(exist_ok=True)

    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')

    if not input_path:
        candidates = sorted(
            INPUT_DIR.glob('*.md'),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            click.echo(
                click.style(
                    f'\n  [ERROR] No input file provided and no Markdown files were found in {INPUT_DIR}\n',
                    fg='red',
                ),
                err=True,
            )
            sys.exit(1)
        input_path = str(candidates[0])

    if not output_path:
        inp = Path(input_path)
        output_path = str(inp.parent / 'output' / f'{inp.stem}.pptx')

    min_s = max(min_slides, slides - 2)
    max_s = min(max_slides, slides + 2)

    click.echo(click.style('\n  MD -> PPTX  (Meridian)\n', fg='cyan', bold=True))
    click.echo(f'  Input  : {input_path}')
    click.echo(f'  Output : {output_path}')
    click.echo(f'  Slides : {min_s}-{max_s}  (target {slides})')
    click.echo(f'  Model  : {model}')
    if api_key:
        click.echo('  Mode   : Gemini structuring + offline fallback\n')
    else:
        click.echo(click.style('  Mode   : Offline fallback (no Gemini API key detected)\n', fg='yellow'))

    try:
        from orchestrator import convert

        out = convert(
            input_path=input_path,
            output_path=output_path,
            api_key=api_key,
            min_slides=min_s,
            max_slides=max_s,
            model_name=model,
            verbose=True,
        )
        click.echo(click.style(f'\n  [OK] Presentation saved to: {out}\n', fg='green', bold=True))
    except FileNotFoundError as exc:
        click.echo(click.style(f'\n  [ERROR] {exc}\n', fg='red'), err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(click.style(f'\n  [ERROR] {exc}\n', fg='red'), err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(click.style(f'\n  [ERROR] Unexpected error: {exc}\n', fg='red'), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
