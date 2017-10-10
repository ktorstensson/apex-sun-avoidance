''' sun_avoidance.py
Script to calculate engineering sun avoidance for given ut date.
'''

import argparse
import ephem as ep
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


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
                        default=pd.datetime.utcnow().date().strftime('%Y-%m-%d'),
                        help='Date (2017-10-10)')
    args = parser.parse_args()
    return args.date


def main(args=None):
    if args is None:
        date = parse_inputs()
    else:
        date = args
    apexobs = ep.Observer()
    apexobs.lon = '-67:45:33.0'
    apexobs.lat = '-23:00:20.8'
    apexobs.elevation = 5105
    apexobs.horizon = ep.degrees(0)
    apexobs.temp = 0
    apexobs.compute_pressure()
    apexobs.name = 'APEX'

    rng = pd.date_range(date, periods=60*24, freq='Min', unit='s', name='utc')
    df = pd.DataFrame(index=rng, columns=['elevation'])
    df.reset_index(inplace=True)

    df['elevation'], df['azimuth'] = zip(*df.utc.apply(sun_pos,
                                                       args=(apexobs,)))
    df.loc[df.azimuth > 180, 'azimuth'] = df.azimuth - 360

    df['clt'] = df.utc - pd.to_timedelta('3H')
    
    df['max_El'] = 150 - df.elevation - 0.0  # Subtracting 0 deg tolerance
    
    df.set_index('clt', inplace=True)
    df.drop(df[df.max_El>90].index, inplace=True)
    
    if df.empty:
        print('No elevation limit on ' + date)
    else:
        fig, ax = plt.subplots(1)
        df.max_El.plot(ax=ax, color='C3')
        ax.fill_between(df.index, df.max_El, 90, color='C3', alpha=0.3)
        plt.grid(which='both')
        plt.ylabel('Max telescope elevation [deg]')
        plt.xlabel('CLT')
        sa_start = df.first_valid_index().strftime("%H:%M")
        sa_end =  df.last_valid_index().strftime("%H:%M")
        ax.text(0.01, 0.05, 'SA starts ' + sa_start,
                transform=ax.transAxes, fontsize='12')
        ax.text(0.98, 0.05, 'SA ends ' + sa_end,
                transform=ax.transAxes, ha='right', fontsize='12')
        ax.text(0.5, 0.15, 'Max El: {:.1f}$^\circ$'.format(df.max_El.min()),
                transform=ax.transAxes, ha='center', fontsize='12')
        plt.title('APEX ' + date)
        plt.tight_layout()
        plot_file = 'plots/maxEl_' + date + '.png'
        plt.savefig(plot_file, bbox_inches='tight', dpi=120)
        print(plot_file)
    
    return


if __name__ == "__main__":
    main()




