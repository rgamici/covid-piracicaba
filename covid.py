#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Projeto para organizar os dados referentes aos casos de coronavírus em
Piracicaba e elaborar gráficos de sua evolução.
'''

import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math


class covid:
    def __init__(self, nome_arquivo):
        self.arquivo = nome_arquivo
        self.nome = nome_arquivo[:-4]
        # processa arquivo de entrada
        [self.data, self.conf] = self.scrap("P")
        [self.data_mort, self.mortes] = self.scrap("M")
        # calcula os números acumulados
        self.acc_conf = self.acumulados(self.data, self.conf)
        self.acc_mort = self.acumulados(self.data_mort, self.mortes)
        # converte a lista de datas em números, começando por 0 para graficos
        self.dias = self.dias_corridos(self.data)
        # calcula o tempo até a primeira morte,
        # necessário para colocar os gráficos juntos
        self.diff_morte = abs((
            datetime.datetime.strptime(self.data_mort[0], "%Y%m%d")
            - datetime.datetime.strptime(self.data[0], "%Y%m%d")).days)

    def scrap(self, mark):
        data = []
        conf = []
        re_pad = re.compile("([0-9]{8}) +" + mark + " +([0-9]+).*")
        ent = open(self.arquivo, 'r')
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

    def acumulados(self, data, conf):
        dia = data[0]
        acc = [0]
        for i in range(len(data)):
            if data[i] == dia:
                acc[-1] += conf[i]
            else:
                acc.append(acc[-1] + conf[i])
        return(acc)

    def dias_corridos(self, data):
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

    def plot_acc_conf(self, x, y, cor, datas, ylabel, fig=None, add=False):
        # Cria gráfico novo se não quiser sobreescrever
        if fig is None:
            fig = plt.figure()
            ax = fig.subplots()
        else:
            if add:
                ax = fig.gca().twinx()
            else:
                ax = fig.gca()
        # plota dados
        ax.scatter(x, y, color=cor)
        # ajusta eixo y
        ax.set_ylabel(ylabel, color=cor)
        ax.tick_params(axis='y', labelcolor=cor)
        ax.set_yscale('log')
        ax.set_ylim(bottom=0.8)
        # altera valores marcados
        _, max_value = ax.get_ylim()
        max_value = int(math.ceil(math.log(max_value, 10)))
        y_ticks = []
        for i in range(max_value):
            for j in [1, 2, 3, 5]:
                y_ticks.append(j * 10 ** i)
        ax.yaxis.set_major_locator(ticker.FixedLocator(y_ticks))
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))
        # ajusta eixo x
        str_data = []
        for data in datas:
            str_data.append(data[6:] + "/" + data[4:6])
        ax.set_xticks(x)
        ax.set_xticklabels(str_data, rotation=90)
        # evita que dados fiquem atrás de outros
        ax.set_zorder(10)
        ax.patch.set_visible(False)
        # adicionar nota sobre último dia
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def plot_conf(self, x, y, cor, datas, ylabel, fig=None, add=False):
        # Cria gráfico novo se não quiser sobreescrever
        if fig is None:
            fig = plt.figure()
            ax = fig.subplots()
        else:
            if add:
                ax = fig.gca().twinx()
            else:
                ax = fig.gca()
        #
        ax.set_ylabel(ylabel, color=cor)
        ax.bar(x, y, color=cor)
        ax.tick_params(axis='y', labelcolor=cor)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        if add:
            ax.set_ylim(0, max(self.conf)*3)
        else:
            str_data = []
            for data in datas:
                str_data.append(data[6:] + "/" + data[4:6])
            ax.set_xticks(x)
            ax.set_xticklabels(str_data, rotation=90)
            # adicionar nota sobre último dia
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def marcar_datas(self, fig):
        ax = fig.gca()
        color = ax.yaxis.label.get_color()
        # definir ticks e posição das linhas relevantes
        # eixo x
        x_ticks = []
        x_labels = []
        vlines_x = []
        vlines_y = []
        for i in range(len(self.dias)):
            if (
                i == 0
                or i == len(self.dias) - 1
                or int(self.data[i]) % 100 == 1
                or int(self.data[i]) % 100 == 15
            ):
                x_ticks.append(self.dias[i])
                x_labels.append(self.data[i][6:] + '/' + self.data[i][4:6])
                vlines_x.append(self.dias[i])
                vlines_y.append(self.acc_conf[i])
        for x, y in zip(vlines_x, vlines_y):
            label = str(y)
            plt.annotate(label, (x, y), textcoords="offset points",
                         xytext=(10, -10), ha='center', color=color)
        plt.xticks(x_ticks, x_labels, rotation=90)
        # eixo y
        _, max_value = ax.get_ylim()
        max_value = int(math.ceil(math.log(max_value, 10)))
        y_ticks = []
        for i in range(max_value):
            for j in [1, 2, 3, 5]:
                y_ticks.append(j * 10 ** i)
        ax.yaxis.set_major_locator(ticker.FixedLocator(y_ticks))
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))
        # marcar valores relevantes
        ax.vlines(vlines_x, [0]*len(vlines_x), vlines_y,
                  linestyles='dashed', color='tab:grey', linewidth=1)
        ax.hlines(vlines_y, [-10]*len(vlines_x), vlines_x,
                  linestyles='dashed', color='tab:grey', linewidth=1)
        ax.set_xlim(left=-1)

    def atualiza_graf(self):
        # gráfico de novos casos
        fig_conf = self.plot_conf(self.dias, self.conf, 'tab:blue',
                                  self.data, 'Novos Casos por Dia')
        fig_add_title(fig_conf, "Novos Casos de Coronavírus em " + self.nome)
        fig_conf.savefig("img/" + self.data[-1] + "-"
                         + self.nome + '-novoscasos.png')
        # gráfico do total de casos
        fig_acc = self.plot_acc_conf(self.dias, self.acc_conf,
                                     'tab:red', self.data, "Total de Casos")
        fig_add_title(fig_acc, "Total de Casos de Coronavírus em " + self.nome)
        fig_acc.savefig("img/" + self.data[-1] + "-"
                        + self.nome + '-totalcasos.png')
        # gráfico com novos casos confirmados e o total acumulado
        fig_both = self.plot_acc_conf(self.dias, self.acc_conf,
                                      'tab:red', self.data, "Total de Casos")
        self.marcar_datas(fig_both)
        self.plot_conf(self.dias, self.conf, 'tab:blue', self.data,
                       'Novos Casos por Dia', fig_both, True)
        fig_add_title(fig_both, "Casos Confirmados de Coronavírus em "
                      + self.nome)
        fig_both.savefig("img/" + self.data[-1] + "-"
                         + self.nome + '-casosconfirmados.png')
        #
        plt.show()


def fig_add_title(fig, title):
    fig.gca().set_title(title)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped


if __name__ == '__main__':
    pir = covid("Piracicaba.txt")
    pir.atualiza_graf()
