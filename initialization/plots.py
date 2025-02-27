import os
from functools import partial
from pylab import *
from oggm.core.flowline import FluxBasedModel, FileModel
from oggm import utils
from matplotlib import cm
import pandas as pd
from copy import deepcopy
#from mpl_toolkits.axes_grid.anchored_artists import AnchoredText
from matplotlib.offsetbox import AnchoredText
import matplotlib as mpl
from matplotlib.collections import LineCollection
from matplotlib.legend_handler import HandlerLineCollection
from matplotlib.ticker import MaxNLocator

FlowlineModel = partial(FluxBasedModel, inplace=False)
pd.options.mode.chained_assignment = None
import warnings

warnings.filterwarnings("ignore")

mpl.rcParams['axes.linewidth'] = 3
mpl.rcParams['xtick.major.width'] = 3
mpl.rcParams['ytick.major.width'] = 3
mpl.rcParams['ytick.minor.width'] = 2
mpl.rcParams['font.size'] = 25
mpl.rcParams['font.weight'] = 'medium'
mpl.rcParams['axes.labelweight'] = 'medium'
mpl.rcParams['legend.fontsize'] = 30
mpl.rcParams['lines.linewidth'] = 3


def add_at(ax, t, loc=2):
    fp = dict(size=15)
    _at = AnchoredText(t, loc=loc, prop=fp, borderpad=0)
    _at.patch.set_linewidth(3)
    ax.add_artist(_at)
    return _at


class HandlerColorLineCollection(HandlerLineCollection):
    def create_artists(self, legend, artist, xdescent, ydescent,
                       width, height, fontsize, trans):
        x = np.linspace(0, width, self.get_numpoints(legend) + 1)
        y = np.zeros(
            self.get_numpoints(legend) + 1) + height / 2. - ydescent
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=artist.cmap,
                            transform=trans)
        lc.set_array(x)
        lc.set_linewidth(artist.get_linewidth())
        return [lc]



def plot_experiment(gdir, ex_mod, t0, te, plot_dir):

    x = np.arange(ex_mod.fls[-1].nx) * ex_mod.fls[-1].dx * \
        ex_mod.fls[-1].map_dx

    fig = plt.figure(figsize=(15, 14))
    grid = plt.GridSpec(2, 1, hspace=0.2, wspace=0.2)
    ax1 = plt.subplot(grid[0, 0])
    ax2 = plt.subplot(grid[1, 0], sharex=ax1)

    if gdir.name != '':
        ax1.set_title(gdir.rgi_id+':'+gdir.name)
    else:
        ax1.set_title(gdir.rgi_id)

    # plot experiments.py, run until ys
    ex_mod = deepcopy(ex_mod)
    ex_mod.reset_y0(t0)
    ex_mod.run_until(t0)
    i = ex_mod.fls[-1].nx
    ax1.plot(x[:i], ex_mod.fls[-1].surface_h[:i], 'k:',
             label=r'$z_{'+str(t0)+'}^{exp}$', linewidth=3)

    ax1.plot(x[:i], ex_mod.fls[-1].bed_h[:i], 'k', label=r'$b$', linewidth=3)

    ex_mod.run_until(te)

    ax2.plot(x[:i], ex_mod.fls[-1].surface_h[:i], 'k:',

             label=r'$z_{'+str(te)+'}^{exp = obs} $', linewidth=3)
    ax2.plot(x[:i], ex_mod.fls[-1].bed_h[:i], 'k', label=r'$b$', linewidth=3)

    # add figure names and legends
    add_at(ax1, r"a", loc=3)
    add_at(ax2, r"b", loc=3)

    ax1.legend(loc=1)
    ax2.legend(loc=1)

    ax1.set_ylabel('Altitude (m)')
    ax1.set_xlabel('Distance along the main flowline (m)')
    ax2.set_ylabel('Altitude (m)')
    ax2.set_xlabel('Distance along the main flowline (m)')

    ax1.tick_params(axis='both', which='major')
    ax2.tick_params(axis='both', which='major')

    plot_dir = os.path.join(plot_dir, '00_synthetic_experiment')
    utils.mkdir(plot_dir)
    fig_name = 'synthetic_experiment_'+str(t0)+'_'+gdir.rgi_id
    plt.savefig(os.path.join(plot_dir, fig_name+'.pdf'), dpi=300)
    plt.savefig(os.path.join(plot_dir, fig_name+'.png'), dpi=300)
    #plt.show()
    #plt.close()



def plot_candidates(gdir, df, yr, step, plot_dir):
    plot_dir = os.path.join(plot_dir, '06_candidates')
    utils.mkdir(plot_dir, reset=False)
    fig, ax = plt.subplots(figsize=(10, 10))

    for file in os.listdir(os.path.join(gdir.dir, str(yr))):

        if file.startswith('model_run'+str(yr)+'_random'):
            suffix = file.split('model_run')[1].split('.nc')[0]
            rp = os.path.join(gdir.dir, str(yr), 'model_run'+suffix+'.nc')
            try:
                fmod = FileModel(rp)
                fmod.volume_km3_ts().plot(ax=ax, color='grey', label='', zorder=1)

            except:
                pass

    # last one again for labeling
    label = r'temperature bias $\in [$' + str(
        df['temp_bias'].min()) + ',' + str(df['temp_bias'].max()) + '$]$'
    df.time = df.time.apply(lambda x: int(x))
    t_eq = df['time'].sort_values().iloc[0]

    df['Fitness value'] = df.fitness

    plt.title(gdir.rgi_id)

    if step == 'step1':
        fmod.volume_km3_ts().plot(ax=ax, color='grey', label=label, zorder=1)
        plt.legend(loc=0, fontsize=28)
        plt.xlabel('Time (years)')
        plt.ylabel(r'Volume $(km^3)$')
        plt.savefig(os.path.join(plot_dir, 'candidates1_' + str(yr) + '_' +
                                 str(gdir.rgi_id) + '.png'), dpi=300)
    elif step == 'step2':
        ax.axvline(x=int(t_eq), color='k', zorder=1, label=r'$t_{stag}$')
        fmod.volume_km3_ts().plot(ax=ax, color='grey', label='', zorder=1)
        # black points
        df.plot.scatter(x='time', y='volume', ax=ax, color='k',
                        label='candidates', s=250, zorder=2)
        plt.legend(loc=0, fontsize=27.5)
        plt.xlabel('Time (years)')
        plt.ylabel(r'Volume $(km^3)$')
        plt.xlim((int(t_eq)-10, 605))
        plt.savefig(os.path.join(plot_dir, 'candidates2_' + str(yr) + '_' +
                                 str(gdir.rgi_id) + '.png'), dpi=300)
    elif step == 'step3':
        fmod.volume_km3_ts().plot(ax=ax, color='grey', label=None, zorder=1)
        ax.axvline(x=int(t_eq), color='k', zorder=1)

        cmap = matplotlib.cm.get_cmap('viridis')
        norm = mpl.colors.LogNorm(vmin=0.01 / 125, vmax=10)

        im = df.plot.scatter(x='time', y='volume', ax=ax, c='Fitness value', colormap='viridis',
                             norm=mpl.colors.LogNorm(vmin=0.01/125, vmax=10, clip=True),
                             s=250, edgecolors='k', zorder=2, colorbar=False)
        # plot again points with objective == 0, without norm
        if len(df[df.fitness == 0]) > 0:
            df[df.fitness == 0].plot.scatter(x='time', y='volume', ax=ax,
                                               c=cmap(0), s=250,
                                               edgecolors='k', zorder=2, colorbar=False)

        plt.xlim(int(t_eq)-10, 605)
        plt.xlabel('Time (years)')
        plt.ylabel(r'Volume $(km^3)$')

        # add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        #cax, kw = mpl.colorbar.make_axes([ax1, ax2, ax3])
        cbar = fig.colorbar(sm, extend='both')
        cbar.ax.tick_params(labelsize=30)
        cbar.set_label('Fitness value', fontsize=30)

        plt.savefig(os.path.join(plot_dir, 'candidates3_' + str(yr) + '_' +
                                 str(gdir.rgi_id) + '.png'), dpi=300)
        #plt.show()

    #plt.close()

    plt.figure(figsize=(15, 14))
    plt.hist(df.volume.values, bins=20)
    plt.xlabel(r'Volume $(km^3)$')
    plt.ylabel(r'Frequency')
    plt.title(gdir.rgi_id)
    plt.savefig(os.path.join(plot_dir, 'hist_candidates' + str(yr) + '_' +
                             str(gdir.rgi_id) + '.png'), dpi=300)
    plt.close()

def plot_fitness_over_time(gdir, df_list, ex_mod, plot_dir):

    from matplotlib.patches import Rectangle

    fig = plt.figure(figsize=(20, 10))
    ax = fig.add_subplot(111, yscale='linear')
    norm = mpl.colors.LogNorm(vmin=0.01/125, vmax=10)
    cmap = matplotlib.cm.get_cmap('viridis')

    volumes = np.linspace(df_list['1850'].volume.min(),
                          df_list['1850'].volume.max(), 100)
    # width of the patches
    yrs = [int(yr) for yr in list(df_list.keys())]
    yrs.sort()
    w = yrs[1] - yrs[0]

    for year, df in df_list.items():
        color = []
        for i in range(len(volumes)):
            if i != len(volumes) - 1:
                part = df[(df.volume >= volumes[i]) & (df.volume <=
                                                       volumes[i + 1])]
                color.append(part.objective.min())
            else:
                part = df[df.volume >= volumes[i]]
                color.append(part.objective.mean())  # or min

        # interpolate missing data
        missing = np.where(np.isnan(color))
        if len(missing[0]) != 0:
            xp = np.delete(range(len(volumes)), missing)
            fp = np.delete(color, missing)
            missing_y = np.interp(missing, xp, fp)
            for i, j in enumerate(missing[0]):
                color[j] = missing_y[0][i]

        year = np.zeros(len(volumes)) + int(year)
        for x, y, c in zip(volumes, year, color):
            if np.isnan(c):
                color = 'white'
            else:
                color = cmap(norm(c))
            ax.add_patch(
                Rectangle((y-(w/2), x), w, volumes[1] - volumes[0],
                          color=color))

    # add experiment in plot
    ex_mod.volume_m3_ts().plot(ax=ax, linestyle=':', color='red')
    ax.set_xlim(yrs[0]-(w/2), yrs[-1]+(w/2))
    ax.set_ylim(volumes[0], volumes[-1])
    plt.title(gdir.rgi_id + ': ' + gdir.name, fontsize=25)
    plt.ylabel(r'Volume ($m^3$)', fontsize=25)
    plt.xlabel(r'Starting time', fontsize=25)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cax, kw = mpl.colorbar.make_axes([ax])
    cbar = fig.colorbar(sm, cax=cax, **kw)
    cbar.ax.tick_params(labelsize=25)
    cbar.set_label('Fitness value', fontsize=25)
    plt.savefig(os.path.join(plot_dir, 'starting' '_' + gdir.rgi_id + '.png'))
    # plt.close()
    # plt.show()


def plot_fitness_values(gdir, df, ex_mod, ys,ye, plot_dir):

    plot_dir = os.path.join(plot_dir, '03_surface_by_fitness')
    utils.mkdir(plot_dir)
    x = (np.arange(ex_mod.fls[-1].nx) * ex_mod.fls[-1].dx * \
        ex_mod.fls[-1].map_dx)/1000
    fig = plt.figure(figsize=(25, 18))
    grid = plt.GridSpec(2, 2, hspace=0.2, wspace=0.2)
    ax1 = plt.subplot(grid[0, 0])
    ax2 = plt.subplot(grid[0, 1], sharey=ax1)
    ax3 = plt.subplot(grid[1, :])

    if gdir.name != '':
        plt.suptitle(gdir.rgi_id + ': ' + gdir.name, fontsize=30)
    elif gdir.rgi_id.endswith('779'):
        plt.suptitle(gdir.rgi_id + ': Guslarferner', fontsize=30)
    else:
        plt.suptitle(gdir.rgi_id, fontsize=30)

    norm = mpl.colors.LogNorm(vmin=0.01/125, vmax=10)
    cmap = matplotlib.cm.get_cmap('viridis')

    # df = df.sort_values('objective', ascending=False)
    df = df.sort_values('fitness', ascending=False)

    for i, model in df['model'].iteritems():
        model = deepcopy(model)
        model.reset_y0(ys)
        # color = cmap(norm(df.loc[i, 'objective']))
        color = cmap(norm(df.loc[i, 'fitness']))
        ax1.plot(x, deepcopy(model.fls[-1].surface_h), color=color,
                 label='')
        model.volume_km3_ts().plot(ax=ax3, color=[color], label='')
        model.run_until(ye)

        ax2.plot(x, model.fls[-1].surface_h, color=color, label='')

    # plot experiments.py
    ex_mod = deepcopy(ex_mod)
    ex_mod.volume_km3_ts().plot(ax=ax3, color='red', linestyle=':',
                               linewidth=3,
                               label='')
    ex_mod.reset_y0(ys)
    ex_mod.run_until(ys)

    ax1.plot(x, ex_mod.fls[-1].surface_h, ':', color='red', label='',
             linewidth=3)
    ax1.plot(x, ex_mod.fls[-1].bed_h, 'k', label='', linewidth=3)

    ex_mod.run_until(ye)

    ax2.plot(x, ex_mod.fls[-1].surface_h, ':', color='red', label='',
             linewidth=3)
    ax2.plot(x, ex_mod.fls[-1].bed_h, 'k', label='',
             linewidth=3)

    # add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cax, kw = mpl.colorbar.make_axes([ax1, ax2, ax3])
    cbar = fig.colorbar(sm, cax=cax, extend='both', **kw)
    cbar.ax.tick_params(labelsize=30)
    cbar.set_label('Fitness value', fontsize=30)

    # add figure names and x-/ylabels
    add_at(ax1, r"a", loc=3)
    add_at(ax2, r"b", loc=3)
    add_at(ax3, r"c", loc=3)

    ax1.set_ylabel('Altitude (m)', fontsize=30)
    ax1.set_xlabel('Distance along the main flowline (km)', fontsize=30)
    ax2.set_ylabel('Altitude (m)', fontsize=30)
    ax2.set_xlabel('Distance along the main flowline (km)', fontsize=30)
    ax3.set_ylabel(r'Volume ($km^3$)', fontsize=30)
    ax3.set_xlabel('Time (years)', fontsize=30)

    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax1.tick_params(axis='both', which='major', labelsize=30)
    ax2.tick_params(axis='both', which='major', labelsize=30)
    ax3.tick_params(axis='both', which='major', labelsize=30)
    ax3.yaxis.offsetText.set_fontsize(30)

    # add legend
    # legend

    t = np.linspace(0, 10, 200)
    x = np.cos(np.pi * t)
    y = np.sin(t)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=cmap,
                        norm=plt.Normalize(0, 10), linewidth=3)
    lc2 = LineCollection(segments, color='k',
                         norm=plt.Normalize(0, 10), linewidth=3)
    lc3 = LineCollection(segments, color='r', linestyle=':',
                         norm=plt.Normalize(0, 10), linewidth=3)

    l1 = ax1.legend(handles=[lc3, lc, lc2], handler_map={
        lc: HandlerColorLineCollection(numpoints=100)},
                    labels=[r'$z_{' + str(ys) + '}^{exp}$',
                            r'$z_{' + str(ys) + '}$',
                            r'$b$'], loc=1)

    l2 = ax2.legend(handles=[lc3, lc, lc2],
                    handler_map={
                        lc: HandlerColorLineCollection(numpoints=100)},
                    labels=[r'$z_{'+str(ye)+'}^{obs}$', r'$z_{'+str(ye)+'}$',
                            r'$b$'], loc=1)

    l3 = ax3.legend(handles=[lc3, lc],
                    handler_map={
                        lc: HandlerColorLineCollection(numpoints=100)},
                    labels=[r'$s_{' + str(ys) + '-' +str(ye)+ '}^{exp}$',
                            r'$s_{' + str(ys) +'-' +str(ye)+
                            '}$'], loc=1)

    l1.set_zorder(1)
    l2.set_zorder(1)
    l3.set_zorder(1)


    ax3.set_xlim(xmin=ys-3, xmax=ye+3)
    fig_name = 'surface_' + str(ys) + '_' + gdir.rgi_id
    #plt.savefig(os.path.join(plot_dir, fig_name + '.pdf'), dpi=300)
    plt.savefig(os.path.join(plot_dir, fig_name + '.png'), dpi=300)
    #plt.show()
    plt.close()



def plot_median(gdir, df, eps, ex_mod, ys, ye, plot_dir):
    plot_dir = os.path.join(plot_dir, '04_median')
    utils.mkdir(plot_dir)
    x = (np.arange(ex_mod.fls[-1].nx) * ex_mod.fls[-1].dx * ex_mod.fls[
        -1].map_dx)/1000
    fig = plt.figure(figsize=(25, 18))
    grid = plt.GridSpec(2, 2, hspace=0.2, wspace=0.2)
    ax1 = plt.subplot(grid[0, 0])
    ax2 = plt.subplot(grid[0, 1], sharey=ax1)
    ax3 = plt.subplot(grid[1, :])

    if gdir.name != '':
        plt.suptitle(gdir.rgi_id + ': ' + gdir.name, fontsize=30)
    elif gdir.rgi_id.endswith('779'):
        plt.suptitle(gdir.rgi_id + ': Guslarferner', fontsize=30)
    else:
        plt.suptitle(gdir.rgi_id, fontsize=30)

    df = df.sort_values('fitness', ascending=False)

    # acceptable glacier states
    df = df[df.fitness <=1]
    s_t0 = pd.DataFrame()
    s_te = pd.DataFrame()
    v = pd.DataFrame()
    for i in df.index:
        model = deepcopy(df.loc[i, 'model'])
        s_t0 = s_t0.append(pd.Series(model.fls[-1].surface_h),
                                 ignore_index=True)
        model.run_until(ye)
        s_te = s_te.append(pd.Series(model.fls[-1].surface_h),
                                 ignore_index=True)
        v = v.append(model.volume_km3_ts(), ignore_index=True)

    ax1.fill_between(x, s_t0.max().values, s_t0.min().values, alpha=0.3, color='grey',
                     label=r'$\mathcal{S}_{' + str(ys) + '}^{' + str(
                         eps) + '}$')
    ax2.fill_between(x, s_te.max().values, s_te.min().values, alpha=0.3, color='grey',
                     label=r'$\mathcal{S}_{' + str(ye) + '}^{' + str(
                         eps) + '}$')
    ax3.fill_between(model.volume_m3_ts().index,
                     v.max().values,
                     v.min().values, alpha=0.3, color='grey',
                     label=r'$\mathcal{S}_{' +str(ys)+'-'+str(ye) +'}^{' + str(eps) + '}$')

    # 5% quantile and median of 5% quantile

    df = df[df.fitness <= df.fitness.quantile(0.05)]
    s_t0 = pd.DataFrame()
    s_te = pd.DataFrame()
    v = pd.DataFrame()
    for i in df.index:
        model = deepcopy(df.loc[i, 'model'])
        s_t0 = s_t0.append(pd.Series(model.fls[-1].surface_h),
                           ignore_index=True)
        model.run_until(ye)
        s_te = s_te.append(pd.Series(model.fls[-1].surface_h),
                           ignore_index=True)
        v = v.append(model.volume_km3_ts(), ignore_index=True)

    ax1.fill_between(x, s_t0.max().values, s_t0.min().values, alpha=0.5,
                     label=r'$Q_{0.05}(\mathcal{S}_{'+str(ys)+'}^{'+str(eps)+'})$')

    ax2.fill_between(x, s_te.max().values, s_te.min().values, alpha=0.5,
                     label=r'$Q_{0.05}(\mathcal{S}_{'+str(ye)+'}^{'+str(eps)+'})$')

    ax3.fill_between(v.columns, v.max().values, v.min().values, alpha=0.5, linewidth=3,
                     label=r'$Q_{0.05}(\mathcal{S}_{'+str(ys)+'-'+str(ye)+'}^{'+str(eps)+'})$')

    # median of 5% quantile
    df.loc[:, 'length'] = df.model.apply(lambda x: x.length_m)
    df = df.sort_values('length', ascending=False)
    l = len(df)
    index = int(l / 2)

    median_model = deepcopy(df.iloc[index].model)
    median_model.volume_km3_ts().plot(ax=ax3, linewidth=3, label=r'$s_{'+str(ys)+'-'+str(ye)+'}^{med}$')
    median_model.reset_y0(ys)
    median_model.run_until(ys)

    ax1.plot(x, median_model.fls[-1].surface_h, label=r'$z_{'+str(ys)+'}^{med}$',
             linewidth=3)
    median_model.run_until(ye)
    ax2.plot(x, median_model.fls[-1].surface_h, label=r'$z_{'+str(ye)+'}^{med}$',
             linewidth=3)

    # min model
    min_mod = deepcopy(df.loc[df.fitness.astype(float).idxmin(), 'model'])
    min_mod.volume_km3_ts().plot(ax=ax3, color='C1',
                                linewidth=3, label=r'$s_{'+str(ys)+'-'+str(ye)+'}^{min}$')
    min_mod.reset_y0(ys)
    min_mod.run_until(ys)

    ax1.plot(x, min_mod.fls[-1].surface_h, 'C1', label=r'$z_{'+str(ys)+'}^{min}$',
             linewidth=3)

    min_mod.run_until(ye)

    ax2.plot(x, min_mod.fls[-1].surface_h, 'C1', label=r'$z_{'+str(ye)+'}^{min}$',
             linewidth=3)

    # experiment
    ex_mod = deepcopy(ex_mod)
    ex_mod.volume_km3_ts().plot(ax=ax3, color='k', linestyle=':',
                               linewidth=3, label=r'$s_{'+str(ys)+'-'+str(ye)+'}^{exp}$')
    ex_mod.reset_y0(ys)
    ex_mod.run_until(ys)

    ax1.plot(x, ex_mod.fls[-1].surface_h, 'k:', label=r'$z_{'+str(ys)+'}^{exp}$',
             linewidth=3)
    ax1.plot(x, ex_mod.fls[-1].bed_h, 'k', label=r'$b$', linewidth=3)

    ex_mod.run_until(ye)

    ax2.plot(x, ex_mod.fls[-1].surface_h, 'k:', label=r'$z_{'+str(ys)+'}^{exp}$',
             linewidth=3)
    ax2.plot(x, ex_mod.fls[-1].bed_h, 'k', label=r'$b$', linewidth=3)

    # add figure names and x-/ylabels
    add_at(ax1, r"a", loc=3)
    add_at(ax2, r"b", loc=3)
    add_at(ax3, r"c", loc=3)

    ax1.set_ylabel('Altitude (m)', fontsize=30)
    ax1.set_xlabel('Distance along the main flowline (km)', fontsize=30)
    ax2.set_ylabel('Altitude (m)', fontsize=30)
    ax2.set_xlabel('Distance along the main flowline (km)', fontsize=30)
    ax3.set_ylabel(r'Volume ($km^3$)', fontsize=30)
    ax3.set_xlabel('Time (years)', fontsize=30)

    ax1.tick_params(axis='both', which='major', labelsize=30)
    ax2.tick_params(axis='both', which='major', labelsize=30)
    ax3.tick_params(axis='both', which='major', labelsize=30)
    ax3.yaxis.offsetText.set_fontsize(30)
    ax3.set_xlim(xmin=ys-3, xmax=ye+3)

    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

    l1 = ax1.legend(loc=1, fontsize=25)
    l1.set_zorder(1)

    l2 = ax2.legend(loc=1, fontsize=25)
    l2.set_zorder(1)

    l3 = ax3.legend(loc=1, fontsize=25)
    l3.set_zorder(1)

    fig_name = 'median_'+str(ys)+'_'+gdir.rgi_id
    plt.savefig(os.path.join(plot_dir, fig_name+'.pdf'), dpi=300)
    #plt.savefig(os.path.join(plot_dir, fig_name+'.png'), dpi=300)
    #plt.show()
    #plt.close()

    return median_model
