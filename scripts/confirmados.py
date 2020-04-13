#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script que gerá um gráfico com o número de casos confirmados
'''

import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math

# data_inicial = '20200325'  # referência para eixo x
arquivo_entrada = '../dados.txt'


def scrap():
    data = []
    conf = []
    re_pad = re.compile("([0-9]{8}) +P +([0-9]+).*")
    ent = open(arquivo_entrada, 'r')
    dados = ent.read()
    matches = re.findall(re_pad, dados)
    for match in matches:
        if data == []:
            data.append(match[0])
            conf.append(int(match[1]))
            continue
        if match[0] == data[-1]:
            conf[-1] += int(match[1])
        else:
            data.append(match[0])
            conf.append(int(match[1]))
    return(data, conf)


def acumulados(data, conf):
    dia = data[0]
    acc = [0]
    for i in range(len(data)):
        if data[i] == dia:
            acc[-1] += conf[i]
        else:
            acc.append(acc[-1] + conf[i])
    return(acc)


def dias_corridos(data):
    dias = [0]
    dia_processado = data[0]
    dia_conv = datetime.datetime.strptime(dia_processado, "%Y%m%d")
    for dia in data:
        if dia != dia_processado:
            conv = datetime.datetime.strptime(dia, "%Y%m%d")
            dias.append(abs(conv - dia_conv).days + dias[-1])
            dia_processado = dia
            dia_conv = conv
    return(dias)


def plot(data, conf):
    fig, ax1 = plt.subplots()
    # calcular dados complementares
    acc = acumulados(data, conf)
    dias = dias_corridos(data)
    # plot do total de casos
    color = 'tab:red'
    # ax1.set_xlabel('data')
    ax1.set_ylabel('Total de Casos', color=color)
    ax1.scatter(dias, acc, color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_yscale('log')
    ax1.set_ylim(bottom=0.8)
    # definir ticks e posição das linhas relevantes
    # eixo x
    x_ticks = []
    x_labels = []
    vlines_x = []
    vlines_y = []
    for i in range(len(dias)):
        if (
            i == 0
            or i == len(dias) - 1
            or int(data[i]) % 100 == 1
            or int(data[i]) % 100 == 15
        ):
            x_ticks.append(dias[i])
            x_labels.append(data[i][6:] + '/' + data[i][4:6])
            vlines_x.append(dias[i])
            vlines_y.append(acc[i])
    for x, y in zip(vlines_x, vlines_y):
        label = str(y)
        plt.annotate(label, (x, y), textcoords="offset points",
                     xytext=(10, -10), ha='center', color=color)
    plt.xticks(x_ticks, x_labels, rotation=90)
    # eixo y
    _, max_value = ax1.get_ylim()
    max_value = int(math.ceil(math.log(max_value, 10)))
    y_ticks = []
    for i in range(max_value):
        for j in [1, 2, 3, 5]:
            y_ticks.append(j * 10 ** i)
    ax1.yaxis.set_major_locator(ticker.FixedLocator(y_ticks))
    ax1.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))
    # marcar valores relevantes
    ax1.vlines(vlines_x, [0]*len(vlines_x), vlines_y,
               linestyles='dashed', color='tab:grey', linewidth=1)
    ax1.hlines(vlines_y, [-10]*len(vlines_x), vlines_x,
               linestyles='dashed', color='tab:grey', linewidth=1)
    ax1.set_xlim(left=-1)
    # cria novo eixo y para novos casos
    ax2 = ax1.twinx()
    # coloca o total de casos por cima
    ax1.set_zorder(10)
    ax1.patch.set_visible(False)
    # plot de novos casos
    color = 'tab:blue'
    ax2.set_ylabel('Novos Casos', color=color)
    ax2.bar(dias, conf, color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 10)
    plt.title("Casos de COVID-19 em Piracicaba")
    # adicionar nota sobre último dia
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
    fig.savefig('../img/confirmados-' + data[-1] + '.png')


if __name__ == '__main__':
    [data, conf] = scrap()
    print("Novos casos por dia")
    print(data, conf)
    acc = acumulados(data, conf)
    print("Total de casos por dia")
    print(data, acc)
    dias = dias_corridos(data)
    plot(data, conf)
