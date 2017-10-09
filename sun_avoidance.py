import ephem as ep
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def sun_pos(date):
    apexobs.date = date
    s = ep.Sun(apexobs)
    el = s.alt * 180 / np.pi
    az = s.az.norm * 180 / np.pi
    return el, az


apexobs = ep.Observer()
apexobs.lon = '-67:45:33.0'
apexobs.lat = '-23:00:20.8'
apexobs.elevation = 5105
apexobs.horizon = ep.degrees(0)
apexobs.temp = 0
apexobs.compute_pressure()
apexobs.name = 'APEX'
apexobs.date = ep.now()
m = ep.Mars(apexobs)
s = ep.Sun(apexobs)

print("Sun", ep.now())
print("Ra/Dec:", s.ra, s.dec)
print("Az/El:", s.az.znorm, s.alt)

ut_date = '2017-10-09'
rng = pd.date_range(ut_date, periods=60*24, freq='Min', unit='s', name='utc')
df = pd.DataFrame(index=rng, columns=['elevation'])
df.reset_index(inplace=True)

df['elevation'], df['azimuth'] = zip(*df.utc.apply(sun_pos))
df.loc[df.azimuth > 180, 'azimuth'] = df.azimuth - 360

df['clt'] = df.utc - pd.to_timedelta('3H')

df['zd'] = 90 - df.elevation
df['max_El'] = 90 - (30 - df.zd) - 0.0  # Subtracting 0 deg tolerance

df.set_index('clt', inplace=True)
df.drop(df[df.max_El>90].index, inplace=True)

fig, ax = plt.subplots(1)
df.max_El.plot(ax=ax, color='C3')
ax.fill_between(df.index, df.max_El, 90, color='C3', alpha=0.3)
plt.grid(which='both')
plt.ylabel('Max telescope elevation [deg]')
plt.xlabel('CLT')
ax.text(0.01, 0.05, 'SA starts ' + df.first_valid_index().strftime("%H:%M"), transform=ax.transAxes, fontsize='12')
ax.text(0.98, 0.05, 'SA ends ' + df.last_valid_index().strftime("%H:%M"), transform=ax.transAxes, ha='right', fontsize='12')
ax.text(0.5, 0.15, 'Max El: {:.1f}$^\circ$'.format(df.max_El.min()), transform=ax.transAxes, ha='center', fontsize='12')
plt.title('APEX ' + df.first_valid_index().strftime("%Y-%m-%d"))
plt.tight_layout()
plt.savefig('plots/maxEl_' + df.first_valid_index().strftime("%Y-%m-%d") + '.png', bbox_inches='tight', dpi=120)
plt.savefig('plots/maxEl_' + df.first_valid_index().strftime("%Y-%m-%d") + '.pdf', bbox_inches='tight', dpi=120)

