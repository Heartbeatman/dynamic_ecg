import numpy as np
import seaborn as sns

import matplotlib.pyplot as plt

def r_plotting(lead):
    '''
    Function to plot the ECG signal and the R peaks
    args:
        lead: the lead to plot
    '''

    plt.figure(figsize=(30,10))
    plt.title(r'$\text{Apple Watch ECG, QRS Detection}$')
    plt.plot(lead.signal,label=r'$\text{Lead 1}$',c='black')
    plt.scatter(lead.r_peaks[:,0],lead.signal[lead.r_peaks[:,0]],c='r',label=r'$\text{R Peaks, N = '+str(len(lead.r_peaks))+'}$')
    plt.xlabel(r'$\text{Samples (n)}$')
    plt.ylabel(r'$\text{Voltage (uV)}$')
    plt.legend(title=r'$'+str(lead.bpm)+'$' + r'$\text{ BPM}$')
    plt.show()


def lorenz_plot(lead):
    '''
    a function to plot the lorenz plot of the RR ints
    '''
    
    plt.clf()
    plt.figure(figsize=(10,10))
    plt.title(r'$\text{Lorenz Plot}$')
    plt.scatter(x = lead.rr_int[:-1],y = lead.rr_int[1:],c='black',s=5,label=r'$\text{RR}_n$' + r'$\text{ vs RR_n+1}$')
    ## add a linear line y =x
    plt.plot([0,lead.rr_int.max()+100],[0,lead.rr_int.max()+100],c='r',label=r'$\text{y=x}$',linestyle='--')
    plt.xlabel(r'$\text{RR}_n$' + r'$\text{ (ms)}$')
    plt.xlim(0,lead.rr_int.max()+100)
    plt.ylabel(r'$\text{RR}_n+1$' + r'$\text{ (ms)}$')
    plt.ylim(0,lead.rr_int.max()+100)
    plt.legend(title=r'$\rho = '+str(np.round(lead.correlation_coefficient,2))+'$')
    plt.show()

 
