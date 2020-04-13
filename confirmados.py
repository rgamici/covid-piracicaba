#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script que gerá um gráfico com o número de casos confirmados
'''

import re
import datetime
import matplotlib.pyplot as plt

data_inicial = '20200325'  # referência para eixo x
arquivo_entrada = 'dados.txt'


def scrap():
    data = [data_inicial]
    conf = [0]
    re_pad = re.compile("([0-9]{8}) +P +([0-9]+).*")
    ent = open(arquivo_entrada, 'r')
    dados = ent.read()
    matches = re.findall(re_pad, dados)
    for match in matches:
        if match[0] == data[-1]:
            conf[-1] += int(match[1])
        else:
            data.append(match[0])
            conf.append(int(match[1]))
    return(data, conf)


def acumulados(data, conf):
    dia = data_inicial
    acc = [0]
    for i in range(len(data)):
        if data[i] == dia:
            acc[-1] += conf[i]
        else:
            acc.append(acc[-1] + conf[i])
    return(acc)


def dias_corridos(data):
    dias = [0]
    dia_processado = data_inicial
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
    ax1.set_xlabel('data')
    ax1.set_ylabel('Total de casos (log)', color=color)
    ax1.scatter(dias, acc, color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_yscale('log')
    # definir ticks
    # marcar valor do último dia
    # cria novo eixo y para novos casos
    ax2 = ax1.twinx()
    # coloca o total de casos por cima
    ax1.set_zorder(10)
    ax1.patch.set_visible(False)
    # plot de novos casos
    color = 'tab:blue'
    ax2.set_ylabel('Novos casos', color=color)
    ax2.bar(dias, conf, color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 10)
    plt.title("Casos de COVID-19 em Piracicaba")
    # adicionar nota sobre último dia
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()


if __name__ == '__main__':
    [data, conf] = scrap()
    print("Novos casos por dia")
    print(data, conf)
    acc = acumulados(data, conf)
    print("Total de casos por dia")
    print(data, acc)
    dias = dias_corridos(data)
    plot(data, conf)
