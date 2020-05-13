''' show_sun_avoidance.py
Script to calculate engineering sun avoidance for given ut date.
'''

import argparse
import ephem as ep
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import os


def sun_pos(date, observer):
    '''Calcalute sun position for given date and observer
    Parameters
    ----------
    date : string
        UT date, e.g. (YYYY-MM-DD)
    observer : ephem.Observer
        observer location

    Returns
    -------
    el, az : float
    '''
    observer.date = date
    s = ep.Sun(observer)
    el = s.alt * 180 / np.pi
    az = s.az.norm * 180 / np.pi
    return el, az


def parse_inputs():
    '''Parse optional date input'''
    parser = argparse.ArgumentParser()
    parser.add_argument('date', nargs='?', type=str,
                        default=dt.datetime.utcnow().date().strftime('%Y-%m-%d'),
                        help='Date (2017-10-10)')
    parser.add_argument('-o', '--offset', type=str,
                        default=get_utc_offset(),
                        help='UT offset e.g. -3, default from www.timeanddate.com')
    args = parser.parse_args()
    return args.date, args.offset


def get_utc_offset(url='https://www.timeanddate.com/time/zone/chile'):
    df = pd.read_html(url)[0]
    offset = df.loc[df[df['Time Zone Abbreviation & Name'] == 'CLT'].index,
                    'Offset'].iloc[0].split()[-1]
    return offset


def ensure_dir(directory):
    if not os.path.exists(directory):
        print('Creating directory ./{:s}'.format(directory))
        os.makedirs(directory)


def main(args=None):
    if args is None:
        date, ut_offset = parse_inputs()
    else:
        date, ut_offset = args
    apexobs = ep.Observer()
    apexobs.lon = '-67:45:33.0'
    apexobs.lat = '-23:00:20.8'
    apexobs.elevation = 5105
    apexobs.horizon = ep.degrees(0)
    apexobs.temp = 0
    apexobs.compute_pressure()
    apexobs.name = 'APEX'

    rng = pd.date_range(date, periods=60*24, freq='Min', name='utc')
    df = pd.DataFrame(index=rng, columns=['elevation'])
    df.reset_index(inplace=True)

    df['elevation'], df['azimuth'] = zip(*df.utc.apply(sun_pos,
                                                       args=(apexobs,)))
    df.loc[df.azimuth > 180, 'azimuth'] = df.azimuth - 360
    print(' - Using CLT: UTC ' + ut_offset + 'H')
    df['clt'] = df.utc + pd.to_timedelta(ut_offset + 'H')

    df['max_El'] = 150 - df.elevation - 0.0  # Subtracting 0 deg tolerance

    df.set_index('clt', inplace=True)
    df.drop(df[df.max_El > 90].index, inplace=True)

    if df.empty:
        print('\nNo elevation limit on ' + date)
    else:
        fig, ax = plt.subplots(1)
        max_el = int(df.max_El.min())
        df.max_El.plot(ax=ax, color='C3')
        ax.fill_between(df.index, df.max_El, 90, color='C3', alpha=0.3)
        plt.grid(which='both')
        plt.ylim(plt.ylim()[0], 90)
        plt.ylabel('Max telescope elevation [deg]')
        plt.xlabel('CLT')
        sa_start = df.first_valid_index().strftime("%H:%M")
        sa_end = df.last_valid_index().strftime("%H:%M")
        ax.text(0.02, 0.05, 'SA starts\n' + sa_start,
                transform=ax.transAxes, fontsize='12')
        ax.text(0.98, 0.05, 'SA ends\n' + sa_end,
                transform=ax.transAxes, ha='right', fontsize='12')
        ax.text(0.5, 0.15, 'Max El: {:d}$^\circ$'.format(max_el),
                transform=ax.transAxes, ha='center', fontsize='12')
        plt.title('APEX ' + date + ' (UT ' + ut_offset + 'H)')
        plt.tight_layout()
        ensure_dir('plots/')
        plot_file = 'plots/maxEl_' + date + '.png'
        plt.savefig(plot_file, bbox_inches='tight', dpi=120)

        ut_start = df.utc.iloc[0].strftime("%H:%M")
        ut_end = df.utc.iloc[-1].strftime("%H:%M")

        print('Figure saved to: ' + plot_file)
        print('\nUTC sun avoidance ' + ' - '.join([ut_start, ut_end]))
        print('CLT sun avoidance ' + ' - '.join([sa_start, sa_end]))
        print('Max elevation {:d} degrees'.format(max_el))
        plt.close('all')
        os.system('display ' + plot_file + '&')

    return df


if __name__ == "__main__":
    df = main()
