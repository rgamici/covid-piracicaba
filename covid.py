#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Projeto para organizar os dados referentes aos casos de coronavírus em
Piracicaba e elaborar gráficos de sua evolução.
'''

import re
import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import math
import urllib.request
import numpy as np
import pylab
import csv

matplotlib.rcParams['font.family'] = "monospace"
plt.rcParams.update({'figure.max_open_warning': 0})


class Covid:
    def __init__(self, nome_arquivo="", nome="", dados_seade=""):
        """
        Parametros:
        -----------
        nome_arquivo: str
            nome do arquivo com os dados de entrada
            Se não for fornecido, usa os dados da SEADE
        nome: str
            nome da cidade a ser exibido nos gráficos e usado para salvar os
            arquivos.
        """
        if nome_arquivo != "":
            self.arquivo = nome_arquivo
        else:
            self.arquivo = None
        if nome == "":
            self.nome = nome_arquivo[:-4]
            self.fonte = "Fonte: Prefeitura de " + self.nome
        else:
            self.nome = nome
            self.fonte = "Fonte: SEADE/SP"
        if nome_arquivo == "":
            # processa dados da SEADE
            (self.data, self.conf,
             self.data_mort, self.mortes) = self.scrap_seade(dados_seade)
        else:
            # processa arquivo de entrada
            [self.data, self.conf] = self.scrap("P")
            [self.data_mort, self.mortes] = self.scrap("M")
        # converte a lista de datas em números,
        # começando por 0 para graficos
        self.dias = self.dias_corridos(self.data)
        self.dias_mort = self.dias_corridos(self.data_mort)
        # calcula o tempo até a primeira morte,
        # necessário para colocar os gráficos juntos
        self.diff_morte = abs((
            datetime.datetime.strptime(self.data_mort[0], "%Y%m%d")
            - datetime.datetime.strptime(self.data[0], "%Y%m%d")).days)
        self.completa_dados()  # preenche lacunas nos dados de mortes
        # calcula os números acumulados
        self.acc_conf = self.acumulados(self.data, self.conf)
        self.acc_mort = self.acumulados(self.data_mort, self.mortes)
        # ### desloca eixo x de mortes
        self.dias_mort_corr = []
        for dia in self.dias_mort:
            self.dias_mort_corr.append(dia + self.diff_morte)
        # calcula média dos últimos 7 dias
        self.med_conf = self.media(self.dias, self.conf)
        self.med_mort = self.media(self.dias_mort, self.mortes)
        self.limpa_datas_marcadas()
        # se usa dados detalhados (não SEADE), cria detalhamentos
        if dados_seade == "":
            self.det_conf = self.scrap_pessoal("P")
            self.det_mort = self.scrap_pessoal("M")

    def scrap(self, mark):
        """ Processa o arquivo de entrada para obter os dados consolidados
        Parametros:
        -----------
        mark: str
            Qual tipo de dado deve ser buscado.
            Tipos usados atualmente `P` para novos casos e `M` para mortes.
        """
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

    def scrap_seade(self, dados_seade):
        datas = []
        conf = []
        data_mort = []
        mortes = []
        acc_conf = 0
        acc_mort = 0
        cidade = self.nome
        for row in dados_seade:
            if row['nome_munic'] == cidade:
                data = datetime.datetime.strftime(
                    datetime.datetime.strptime(row['datahora'],
                                               "%Y-%m-%d"), "%Y%m%d")
                if row['casos'] != "NA":
                    if len(datas) == 0 and int(row['casos']) == 0:
                        # ignora quando ainda não há casos
                        pass
                    else:
                        datas.append(data)
                        conf.append(int(row['casos']) - acc_conf)
                        acc_conf = int(row['casos'])
                if row['obitos'] != "NA":
                    if len(data_mort) == 0 and int(row['obitos']) == 0:
                        pass
                    else:
                        morte = int(row['obitos'])
                        data_mort.append(data)
                        mortes.append(morte - acc_mort)
                        acc_mort = morte
        return(datas, conf, data_mort, mortes)

    def completa_dados(self):
        """ Adiciona valores 0 para datas não reportadas

        Essa função evita que entradas reportadando 0 mortes sejam inseridas
        nos arquivos de entrada e mantendo-o o menos poluído.
        **Lembrete**: Se não há dados referentes a alguma data é porque não
        foi reportado nada, o que ocorre nos fins de semana.
        Para casos confirmados, deve-se inserir uma entrada com 0 casos novos
        para indicar que não houve novos casos reportados.
        """
        dias_completo = []
        data_completo = []
        mort_completo = []
        primeiro_dia = datetime.datetime.strptime(self.data_mort[0],
                                                  "%Y%m%d")
        um_dia = datetime.timedelta(days=1)
        for i in range(max(self.dias_mort[-1], self.dias[-1] - self.diff_morte)
                       + 1):
            dias_completo.append(i)
            if i in self.dias_mort:
                index = self.dias_mort.index(i)
                data_completo.append(self.data_mort[index])
                mort_completo.append(self.mortes[index])
            else:
                data_completo.append((primeiro_dia
                                      + i * um_dia).strftime("%Y%m%d"))
                mort_completo.append(0)
        self.dias_mort = dias_completo
        self.data_mort = data_completo
        self.mortes = mort_completo

    def acumulados(self, data, conf):
        """ Calcula o total acumulado dos dados
        Parametros:
        -----------
        data: lista de dias
        conf: lista de casos
        """
        dia = data[0]
        acc = [0]
        for i in range(len(data)):
            if data[i] == dia:
                acc[-1] += conf[i]
            else:
                acc.append(acc[-1] + conf[i])
        return(acc)

    def dias_corridos(self, data):
        """ Converte a lista de datas em uma lista de integers
        Parametros:
        -----------
        data: lista de datas
        """
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

    def media(self, dias, dados):
        """ Calcula a média dos últimos 7 dias
        Parametros:
        -----------
        dias: lista de inteiros com índices para as datas
        dados: contagem de casos ou mortes
        """
        media = []
        for dia in dias:
            soma = 0
            count = 0
            for i in range(max(0, dia - 6), min(dia + 1, len(dados))):
                soma += dados[i]
                count += 1
            if count == 0:
                count = 1
            media.insert(dia, soma/count)
        return(media)

    def plot_acc_conf(self, x, y, cor, datas, ylabel, fig=None, add=False):
        """ Plota o número total de casos

        Se nenhuma figura for especificada, cria uma novas.
        Se add for True, cria eixos separados para os dados

        Parametros:
        -----------
        x: lista de ints
        y: lista de ints
        cor: str
        datas: lista de str
            Rótulos que serão exibidos no eixo x
        ylabel: str
            Texto a ser utilizado no eixo y
        fig: matplotlib.pyplot.figure
        add: bool
            Cria ou não um novo conjunto de eixos para os dados
        """
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
        # fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def plot_conf(self, x, y, cor, y_med, cor_med, datas, ylabel,
                  fig=None, add=False):
        """ Plota o número de novos casos

        Se nenhuma figura for especificada, cria uma novas.
        Se add for True, cria eixos separados para os dados

        Parametros:
        -----------
        x: lista de ints
        y: lista de ints
        cor: str
        y_med: lista de médias
        cor_med : cor da linha das médias
        datas: lista de str
            Rótulos que serão exibidos no eixo x
        ylabel: str
            Texto a ser utilizado no eixo y
        fig: matplotlib.pyplot.figure
        add: bool
            Cria ou não um novo conjunto de eixos para os dados
        """
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
        ax.plot(x, y_med, color=cor_med)
        ax.tick_params(axis='y', labelcolor=cor)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        if add:
            ax.set_ylim(0, max(y)*3)
        else:
            str_data = []
            for data in datas:
                str_data.append(data[6:] + "/" + data[4:6])
            ax.set_xticks(x)
            ax.set_xticklabels(str_data, rotation=90)
            # adicionar nota sobre último dia
        # fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def marcar_datas(self, fig, x_axis, y_axis, labels, color=''):
        """ Adiciona marcações nos dados com certa frequencia

        As marcas são adicionadas no primeiro valor e no último, assim como nos
        referentes ao primeiro dia de cada mês, e do 15º dia.

        Essa função também adiciona dados nas variáveis `datas_marcadas_i`
        e `datas_marcadas_i` para o caso de mais de um conjunto de dados ser
        utilizado, o que fará com que seja necessário ajustar os rótulos no
        eixo x com a função `ajusta_eixo_x()`.

        Parametros:
        -----------
        fig: matplotlib.pyplot.figure
        x_axis: list of ints
        y_axis: list of ints
        label: list of str
            Rótulos usados nos dados do eixo x
        """
        ax = fig.gca()
        if color == '':
            color = ax.yaxis.label.get_color()
        # definir ticks e posição das linhas relevantes
        # eixo x
        x_ticks = []
        x_labels = []
        vlines_x = []
        vlines_y = []
        for i in range(len(x_axis)):
            if (
                i == 0
                or i == len(x_axis) - 1
                or int(labels[i]) % 100 == 1
                or int(labels[i]) % 100 == 15
            ):
                x_ticks.append(x_axis[i])
                x_labels.append(labels[i][6:] + '/' + labels[i][4:6])
                vlines_x.append(x_axis[i])
                vlines_y.append(y_axis[i])
                self.datas_marcadas_i.append(x_axis[i])
                self.datas_marcadas.append(labels[i][6:] + '/'
                                           + labels[i][4:6])
        for x, y in zip(vlines_x, vlines_y):
            label = str(int(y))
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

    def limpa_datas_marcadas(self):
        """ Reseta as variaveis referentes as datas a serem marcadas"""
        self.datas_marcadas_i = []
        self.datas_marcadas = []

    def ajusta_eixo_x(self, fig, x, datas):
        """ Ajusta a escala e os ticks a serem exibidos

        Essa função precisa ser executada caso o segundo conjunto de dados
        contenha mais dados do que o originalmente plotado.
        Ela também adiciona os rótulos no eixo x para todas as marcações.
        """
        # ajusta eixo x
        ax = fig.gca()
        ax.set_xlim(min(x) - 1, max(x) + 1)
        unicos_i = []
        unicos = []
        for i in self.datas_marcadas_i:
            if i not in unicos_i:
                index = self.datas_marcadas_i.index(i)
                unicos_i.append(self.datas_marcadas_i[index])
                unicos.append(self.datas_marcadas[index])
        ax.set_xticks(unicos_i)
        ax.set_xticklabels(unicos, rotation=90)

    def fig_add_fonte(self, fig):
        """ Adiciona a fonte dos dados no canto"""
        fig.text(1, 0, self.fonte, fontsize=7, horizontalalignment='right',
                 verticalalignment='bottom')
        fig.tight_layout()

    def graf_conf(self):
        fig_conf = self.plot_conf(self.dias, self.conf, 'tab:blue',
                                  self.med_conf, 'tab:purple',
                                  self.data, 'Novos Casos por Dia')
        fig_add_title(fig_conf, "Novos Casos de Coronavírus em " + self.nome)
        self.fig_add_fonte(fig_conf)
        return fig_conf

    def graf_conf_acc(self):
        fig_acc = self.plot_acc_conf(self.dias, self.acc_conf,
                                     'tab:red', self.data, "Total de Casos")
        fig_add_title(fig_acc, "Total de Casos de Coronavírus em " + self.nome)
        self.fig_add_fonte(fig_acc)
        return(fig_acc)

    def graf_conf_both(self):
        fig_both = self.plot_acc_conf(self.dias, self.acc_conf,
                                      'tab:red', self.data, "Total de Casos")
        self.marcar_datas(fig_both, self.dias, self.acc_conf, self.data)
        self.plot_conf(self.dias, self.conf, 'tab:blue',
                       self.med_conf, 'tab:purple', self.data,
                       'Novos Casos por Dia', fig_both, True)
        fig_add_title(fig_both, "Casos Confirmados de Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_both)
        return(fig_both)

    def graf_mort(self):
        fig_mort = self.plot_conf(self.dias_mort, self.mortes, 'tab:orange',
                                  self.med_mort, 'tab:brown',
                                  self.data_mort, 'Mortes por dia')
        fig_add_title(fig_mort, "Número de Mortes por Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_mort)
        return(fig_mort)

    def graf_mort_acc(self):
        fig_acc_mort = self.plot_acc_conf(self.dias_mort, self.acc_mort,
                                          'black', self.data_mort,
                                          "Total de Mortes")
        fig_add_title(fig_acc_mort, "Total de Mortes por Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_acc_mort)
        return(fig_acc_mort)

    def graf_mort_both(self):
        fig_both_mort = self.plot_acc_conf(self.dias_mort, self.acc_mort,
                                           'black', self.data_mort,
                                           "Total de Mortes")
        self.marcar_datas(fig_both_mort, self.dias_mort, self.acc_mort,
                          self.data_mort)
        self.plot_conf(self.dias_mort, self.mortes, 'tab:orange',
                       self.med_mort, 'tab:brown', self.data_mort,
                       'Novas Mortes por Dia', fig_both_mort, True)
        fig_add_title(fig_both_mort, "Mortes por Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_both_mort)
        return(fig_both_mort)

    def graf_all(self):
        # ### cria gráfico e plota total de casos
        fig_all = self.plot_acc_conf(self.dias, self.acc_conf,
                                     'tab:red', self.data, "")
        self.limpa_datas_marcadas()
        self.marcar_datas(fig_all, self.dias, self.acc_conf, self.data)
        # ### adiciona dados referentes às mortes
        self.plot_acc_conf(self.dias_mort_corr, self.acc_mort,
                           'black', self.data_mort,
                           "Total de Casos e Mortes", fig_all)
        self.marcar_datas(fig_all, self.dias_mort_corr, self.acc_mort,
                          self.data_mort)
        # ### adiciona os dados de novos casos e mortes por dia
        self.plot_conf(self.dias, self.conf, 'tab:blue',
                       self.med_conf, 'tab:purple', self.data,
                       '', fig_all, True)
        self.plot_conf(self.dias_mort_corr, self.mortes, 'tab:orange',
                       self.med_mort, 'tab:brown', self.data_mort,
                       'Novos Casos e Mortes por Dia', fig_all, False)
        # ### ajustes e título
        self.ajusta_eixo_x(fig_all, self.dias + self.dias_mort_corr,
                           self.data + self.data_mort)
        handles = [mlines.Line2D([], [], color='tab:red', marker="o",
                                 linestyle="None", label="Total de Casos"),
                   mlines.Line2D([], [], color='black', marker="o",
                                 linestyle="None", label="Total de Mortes"),
                   mpatches.Patch(color='tab:blue', label="Novos Casos"),
                   mpatches.Patch(color='tab:orange', label="Novas Mortes")]
        ax = fig_all.gca()
        ax.legend(handles=handles, loc="upper left")
        fig_add_title(fig_all, "Casos Confirmados e Mortes por Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_all)
        return(fig_all)

    def atualiza_graf(self, save=False, show=False, atualiza_texto=False):
        """ Gera todos os gráficos e mostra/salva-os.

        Parametros:
        -----------
        save: bool
            Flag para indicar se os arquivos com as datas nos nomes devem
            ser salvos ou não.
        show: bool
            Flag para indicar se os gráficos devem ser exibidos ou não.
        atualiza_texto: bool
            Flag para indicar se os arquivos **sem** as datas nos nomes devem
            ser salvos ou não.
            Esse arquivos são referenciados pelas páginas, que apontam para os
            mais recentes.
        """
        print("Gerando gráficos de casos e óbitos")
        # GRÁFICOS DE CASOS CONFIRMADOS
        fig_conf = self.graf_conf()  # gráfico de novos casos
        fig_acc = self.graf_conf_acc()  # gráfico do total de casos
        fig_both = self.graf_conf_both()  # gráfico com novos casos e total
        # GRÁFICOS COM MORTES
        fig_mort = self.graf_mort()  # gráfico com o número de mortes por dia
        fig_acc_mort = self.graf_mort_acc()  # gráfico com o total de mortes
        fig_both_mort = self.graf_mort_both()
        # GRÁFICO COM CASOS CONFIRMADOS E MORTES
        fig_all = self.graf_all()
        # salva figuras
        nome = self.nome.replace(' ', '_')
        if self.arquivo:
            sufixo = ""
        else:
            sufixo = "-SEADE"
        if save:
            fig_conf.savefig("img/" + self.data[-1] + "-"
                             + nome + '-novoscasos' + sufixo + '.png')
            fig_acc.savefig("img/" + self.data[-1] + "-"
                            + nome + '-totalcasos' + sufixo + '.png')
            fig_both.savefig("img/" + self.data[-1] + "-" + nome +
                             '-casosconfirmados' + sufixo + '.png')
            fig_mort.savefig("img/" + self.data_mort[-1] + "-" + nome
                             + '-novasmortes' + sufixo + '.png')
            fig_acc_mort.savefig("img/" + self.data_mort[-1] + "-" + nome
                                 + '-totalmortes' + sufixo + '.png')
            fig_both_mort.savefig("img/" + self.data_mort[-1] + "-"
                                  + nome + '-mortes' + sufixo + '.png')
            data = max(self.data[-1], self.data_mort[-1])
            fig_all.savefig("img/" + data + "-" + nome + ''
                            + sufixo + '.png')
        if atualiza_texto:
            fig_conf.savefig("img/" + nome + '-novoscasos'
                             + sufixo + '.png')
            fig_acc.savefig("img/" + nome + '-totalcasos'
                            + sufixo + '.png')
            fig_both.savefig("img/" + nome + '-casosconfirmados'
                             + sufixo + '.png')
            fig_mort.savefig("img/" + nome + '-novasmortes'
                             + sufixo + '.png')
            fig_acc_mort.savefig("img/" + nome + '-totalmortes'
                                 + sufixo + '.png')
            fig_both_mort.savefig("img/" + nome + '-mortes'
                                  + sufixo + '.png')
            fig_all.savefig("img/" + nome + sufixo + '.png')
        if show:
            plt.show()

    def scrap_pessoal(self, marcador):
        data = []
        quant = []
        sexo = []
        idade = []
        re_pad = re.compile("([0-9]{8}) +" + marcador + " +([0-9]+) +"
                            "([MF-]) +([0-9-]+).*")
        ent = open(self.arquivo, 'r')
        dados = ent.read()
        matches = re.findall(re_pad, dados)
        for match in matches:
            if data == []:
                data.append(match[0])
                quant.append(int(match[1]))
                sexo.append(match[2])
                idade.append(int(match[3]))
                continue
            if (match[0] == data[-1] and match[2] == sexo[-1]
                    and match[3] == idade[-1]):
                quant[-1] += int(match[1])
            else:
                data.append(match[0])
                quant.append(int(match[1]))
                sexo.append(match[2])
                if match[3][0] == "-":
                    idade.append(-1)
                else:
                    idade.append(int(match[3]))
        return({"data": data, "quant": quant, "sexo": sexo, "idade": idade})

    def graf_detalhes(self, mostra=False, salva=False):
        # initicalização
        print("Gerando gráficos com detalhamento por sexo e idade")
        idades = np.arange(11)  # mais de 90 na mesma categoria
        labels = ['-', '0-9', '10-19', '20-29', '30-39', '40-49',
                  '50-59', '60-69', '70-79', '80-89', '90-']
        conf_m = [0]*11
        mort_m = [0]*11
        recu_m = [0]*11
        conf_f = [0]*11
        mort_f = [0]*11
        recu_f = [0]*11
        conf_x = [0]*11
        mort_x = [0]*11
        recu_x = [0]*11
        # calcula data para recuperados (14 dias)
        data = datetime.datetime.strptime(self.det_conf["data"][-1], "%Y%m%d")
        rec = datetime.timedelta(days=14)
        data_rec = datetime.datetime.strftime(data - rec, "%Y%m%d")
        # Separa os casos confirmados or sexo e idade
        for i in range(len(self.det_conf["data"])):
            idade = self.det_conf["idade"][i] // 10 + 1
            if idade > 10:  # mais de 90 anos ficam em um só grupo
                idade = 10
            if self.det_conf["sexo"][i] == "M":
                conf_m[idade] += self.det_conf["quant"][i]
                if self.det_conf["data"][i] < data_rec:
                    recu_m[idade] += self.det_conf["quant"][i]
            elif self.det_conf["sexo"][i] == "F":
                conf_f[idade] += self.det_conf["quant"][i]
                if self.det_conf["data"][i] < data_rec:
                    recu_f[idade] += self.det_conf["quant"][i]
            else:
                conf_x[idade] += self.det_conf["quant"][i]
                if self.det_conf["data"][i] < data_rec:
                    recu_x[idade] += self.det_conf["quant"][i]
        # separa os óbitos por sexo e idade
        for i in range(len(self.det_mort["data"])):
            idade = self.det_mort["idade"][i] // 10 + 1
            if idade > 10:
                idade = 10
            if self.det_mort["sexo"][i] == "M":
                mort_m[idade] += self.det_mort["quant"][i]
                recu_m[idade] -= self.det_mort["quant"][i]
            elif self.det_mort["sexo"][i] == "F":
                mort_f[idade] += self.det_mort["quant"][i]
                recu_f[idade] -= self.det_mort["quant"][i]
            else:
                mort_x[idade] += self.det_mort["quant"][i]
                recu_x[idade] -= self.det_mort["quant"][i]
        for i in range(len(recu_m)):
            if recu_m[i] < 0:
                recu_m[i] = 0
            if recu_f[i] < 0:
                recu_f[i] = 0
            if recu_x[i] < 0:
                recu_x[i] = 0
        # calcula os totais de casos
        tot_conf_m = sum(conf_m)
        tot_conf_f = sum(conf_f)
        tot_conf_x = sum(conf_x)
        tot_conf = tot_conf_m + tot_conf_f + tot_conf_x
        tot_mort_m = sum(mort_m)
        tot_mort_f = sum(mort_f)
        tot_mort_x = sum(mort_x)
        tot_mort = tot_mort_m + tot_mort_f + tot_mort_x
        tot_recu_m = sum(recu_m)
        tot_recu_f = sum(recu_f)
        tot_recu_x = sum(recu_x)
        tot_recu = tot_recu_m + tot_recu_f + tot_recu_x
        # calcula o total por idade
        conf = [0]*11
        mort = [0]*11
        recu = [0]*11
        for i in range(len(conf_m)):
            conf[i] = conf_m[i] + conf_f[i] + conf_x[i]
            mort[i] = mort_m[i] + mort_f[i] + mort_x[i]
            recu[i] = recu_m[i] + recu_f[i] + recu_x[i]
        # variáveis para os gráficos
        width = .25
        cor_h = "blue"
        cor_m = "red"
        cor_x = "orange"
        cor_conf = "tab:red"
        cor_mort = "black"
        cor_recu = "tab:green"
        # plota gráfico de casos confirmados por sexo e idade
        fig_conf = plt.figure()
        ax = fig_conf.subplots()
        rects_x = ax.bar(idades - width, conf_x, width,
                         label="Não identificado", color=cor_x)
        rects_m = ax.bar(idades, conf_m, width, label="Homens", color=cor_h)
        rects_f = ax.bar(idades + width, conf_f, width,
                         label="Mulheres", color=cor_m)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            taxa = int(conf[i]/tot_conf * 100)
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_xlabel("Idade / Prevalência")
        ax.set_ylabel("Número de casos confirmados")
        tit = "Casos confirmados de Coronavírus em "
        fig_add_title(fig_conf, tit + self.nome)
        fig_conf.tight_layout()
        plt.legend()
        # plota gráfico de óbitos por sexo e idade
        fig_mort = plt.figure()
        ax = fig_mort.subplots()
        rects_x = ax.bar(idades - width, mort_x, width,
                         label="Não identificado", color=cor_x)
        rects_m = ax.bar(idades, mort_m, width, label="Homens", color=cor_h)
        rects_f = ax.bar(idades + width, mort_f, width,
                         label="Mulheres", color=cor_m)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            taxa = int(mort[i]/tot_mort * 100)
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_xlabel("Idade / Prevalência")
        ax.set_ylabel("Número de óbitos")
        tit = "Mortes por Coronavírus em "
        fig_add_title(fig_mort, tit + self.nome)
        fig_mort.tight_layout()
        plt.legend()
        # plota gráfico de recuperados por sexo e idade
        fig_recu = plt.figure()
        ax = fig_recu.subplots()
        rects_x = ax.bar(idades - width, recu_x, width,
                         label="Não identificado", color=cor_x)
        rects_m = ax.bar(idades, recu_m, width, label="Homens", color=cor_h)
        rects_f = ax.bar(idades + width, recu_f, width,
                         label="Mulheres", color=cor_m)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            taxa = int(recu[i]/tot_recu * 100)
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Idade / Prevalência")
        ax.set_ylabel("Número de recuperados")
        tit = "Pacientes recuperados de Coronavírus em "
        fig_add_title(fig_recu, tit + self.nome)
        fig_recu.tight_layout()
        plt.legend()
        # plota gráfico de homens por idade
        fig_m = plt.figure()
        ax = fig_m.subplots()
        rects_x = ax.bar(idades - width, conf_m, width,
                         label="Casos Confirmados", color=cor_conf)
        rects_m = ax.bar(idades, recu_m, width, label="Recuperados",
                         color=cor_recu)
        rects_f = ax.bar(idades + width, mort_m, width,
                         label="Óbitos", color=cor_mort)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            if mort_m[i] != 0:
                taxa = int(mort_m[i] / (mort_m[i] + recu_m[i]) * 100)
            else:
                taxa = 0
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Idade / Mortalidade")
        ax.set_ylabel("Número de pacientes")
        tit = "Estado de Homens com Coronavírus em "
        fig_add_title(fig_m, tit + self.nome)
        fig_m.tight_layout()
        plt.legend()
        # plota gráfico de mulheres por idade
        fig_f = plt.figure()
        ax = fig_f.subplots()
        rects_x = ax.bar(idades - width, conf_f, width,
                         label="Casos Confirmados", color=cor_conf)
        rects_m = ax.bar(idades, recu_f, width, label="Recuperadas",
                         color=cor_recu)
        rects_f = ax.bar(idades + width, mort_f, width,
                         label="Óbitos", color=cor_mort)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            if mort_f[i] != 0:
                taxa = int(mort_f[i] / (mort_f[i] + recu_f[i]) * 100)
            else:
                taxa = 0
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Idade / Mortalidade")
        ax.set_ylabel("Número de pacientes")
        tit = "Estado de Mulheres com Coronavírus em "
        fig_add_title(fig_f, tit + self.nome)
        fig_f.tight_layout()
        plt.legend()
        # plota gráfico por idade
        fig_t = plt.figure()
        ax = fig_t.subplots()
        rects_x = ax.bar(idades - width, conf, width,
                         label="Casos Confirmados", color=cor_conf)
        rects_m = ax.bar(idades, recu, width, label="Recuperados",
                         color=cor_recu)
        rects_f = ax.bar(idades + width, mort, width,
                         label="Óbitos", color=cor_mort)
        ax.set_xticks(idades)
        label_temp = []
        for i in range(len(conf)):
            if mort[i] != 0:
                taxa = int(mort[i] / (mort[i] + recu[i]) * 100)
            else:
                taxa = 0
            taxa = str(taxa) + "%"
            label_temp.append(labels[i] + '\n' + taxa)
        ax.set_xticklabels(label_temp)
        autolabel(ax, rects_m)
        autolabel(ax, rects_f)
        autolabel(ax, rects_x)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Idade / Mortalidade")
        ax.set_ylabel("Número de pacientes")
        tit = "Estado de Pacientes com Coronavírus em "
        fig_add_title(fig_t, tit + self.nome)
        fig_t.tight_layout()
        plt.legend()

        # Salva e mostra as figuras
        if salva:
            nome = self.nome.replace(' ', '_')
            fig_conf.savefig("img/" + nome + '-det-confirmados.png')
            fig_mort.savefig("img/" + nome + '-det-mortes.png')
            fig_recu.savefig("img/" + nome + '-det-recuperados.png')
            fig_m.savefig("img/" + nome + '-det-homens.png')
            fig_f.savefig("img/" + nome + '-det-mulheres.png')
            fig_t.savefig("img/" + nome + '-det-total.png')
        if mostra:
            plt.show()

    def fit(self, periodo=-1, proj=28):
        # filtra dados do últimos n dias
        if periodo == -1:
            dias = self.dias[:]
            conf = self.acc_conf[:]
            dias_m = self.dias_mort_corr[:]
            mort = self.acc_mort[:]
            periodo = len(dias)
        else:
            dias = []
            conf = []
            dias_m = []
            mort = []
            for i in range(len(self.dias)):
                if self.dias[i] > self.dias[-1] - periodo - 1:
                    dias.append(self.dias[i])
                    conf.append(self.acc_conf[i])
            for i in range(len(self.dias_mort_corr)):
                if self.dias_mort_corr[i] > (self.dias_mort_corr[-1]
                                             - periodo - 1):
                    dias_m.append(self.dias_mort_corr[i])
                    mort.append(self.acc_mort[i])
        # regressões  y = b.e^ax
        (a_c, b_c) = pylab.polyfit(dias, np.log(conf), 1)
        (a_m, b_m) = pylab.polyfit(dias_m, np.log(mort), 1)
        # transforma b
        b_c = math.exp(b_c)
        b_m = math.exp(b_m)
        # gera dados para plotar regressões
        x = np.linspace(min(max(dias[0] - 3 * (dias[-1] - dias[0]),
                                self.dias[0]),
                            self.dias[0]),
                        dias[-1] + proj)
        y_c = []
        y_m = []
        for i in x:
            y_c.append(b_c * math.exp(a_c * i))
            y_m.append(b_m * math.exp(a_m * i))
            # gerar datas para marcação
        # calcula outros dados
        dobro_c = math.log(2) / a_c
        dobro_m = math.log(2) / a_m
        cresc_c = math.exp(a_c * 30)
        cresc_m = math.exp(a_m * 30)
        # plota grafico
        # plota casos confirmados e regresssão
        fig_fit = self.plot_acc_conf(self.dias, self.acc_conf,
                                     'tab:red', self.data, "Total de Casos")
        ax_conf = fig_fit.gca()
        ax_conf.plot(x, y_c, linestyle='--', color='tab:orange')
        ax_conf.set_ylim(top=max(y_c)*2)
        corrige_y(ax_conf)
        # novo eixo e plota mortes e regressão
        self.plot_acc_conf(self.dias_mort_corr, self.acc_mort,
                           'black', self.data_mort,
                           "Total de Mortes", fig_fit, True)
        ax_mort = fig_fit.gca()
        ax_mort.plot(x, y_m, linestyle='--', color='tab:blue')
        ax_mort.set_ylim(top=ax_conf.get_ylim()[1])
        corrige_y(ax_mort)
        # marca datas relevantes
        x_tick = []
        x_label = []
        vlines_x = []
        vlines_y = []
        # dados
        for i in range(0, len(dias)):
            if i % 7 == 0 or i == len(dias)-1:
                x_tick.append(dias[i])  # para conf e mort
                x_label.append(gera_data(dias[i], self.dias[-1],
                                         self.data[-1]))
                vlines_x.append([dias[i]]*2)
                vlines_y.append(conf[i])
                vlines_y.append(mort[i])
                plt.annotate(str(int(conf[i])), (dias[i], conf[i]),
                             textcoords="offset points",
                             xytext=(10, -10), ha='center', color='tab:red')
                plt.annotate(str(int(mort[i])), (dias[i], mort[i]),
                             textcoords="offset points",
                             xytext=(10, -10), ha='center', color='black')
        for i in range(7, proj+1, 7):
            dia = dias[-1] + i
            x_tick.append(dia)  # para conf e mort
            x_label.append(gera_data(dia, self.dias[-1],
                                     self.data[-1]))
            vlines_x.append([dia]*2)
            calc_c = b_c * math.exp(a_c * dia)
            calc_m = b_m * math.exp(a_m * dia)
            vlines_y.append(calc_c)
            vlines_y.append(calc_m)
            plt.annotate(str(int(calc_c)), (dia, calc_c),
                         textcoords="offset points",
                         xytext=(-2, 2), ha='right', color='tab:orange')
            plt.annotate(str(int(calc_m)), (dia, calc_m),
                         textcoords="offset points",
                         xytext=(-2, 2), ha='right', color='tab:blue')
        for tick in x_tick:
            # anotar dados
            plt.xticks(x_tick, x_label, rotation=90)
        ax_conf.vlines(vlines_x, [0]*len(vlines_x), vlines_y,
                       linestyles='dashed', color='tab:grey', linewidth=1)
        # Adiciona zoom das regressões
        # zoom conf
        axins = ax_conf.inset_axes([0.05, 0.6, 0.25, 0.3])
        # sub region of the original image
        axins.scatter(dias, conf, color='tab:red', s=10)
        axins.plot(x, y_c, linestyle='--', color='tab:orange')
        x1, x2 = dias[0]-periodo*1/7, dias[-1]+periodo*1/7
        y1, y2 = conf[0]*.9, conf[-1]*1.1
        axins.set_yscale('log')
        axins.set_xlim(x1, x2)
        axins.set_ylim(y1, y2)
        axins.tick_params(which="both", bottom=False, left=False,
                          labelbottom=False, labelleft=False)
        # zoom mortes
        axins2 = ax_conf.inset_axes([0.7, 0.02, 0.25, 0.3])
        # sub region of the original image
        axins2.scatter(dias_m, mort, color='black', s=10)
        axins2.plot(x, y_m, linestyle='--', color='tab:blue')
        x1, x2 = dias_m[0]-periodo*1/7, dias_m[-1]+periodo*1/7
        y1, y2 = mort[0]*.9, mort[-1]*1.1
        axins2.set_yscale('log')
        axins2.set_xlim(x1, x2)
        axins2.set_ylim(y1, y2)
        axins2.tick_params(which="both", bottom=False, left=False,
                           labelbottom=False, labelleft=False)
        # título
        ax_conf.set_title("Projeção de novos casos e mortes em " + self.nome)
        fig_fit.text(0.5, 0.92, "Período de análise: " + str(periodo) +
                     " dias, Projeção: " + str(proj) + " dias", fontsize=10,
                     horizontalalignment='center',
                     verticalalignment='top')
        self.fig_add_fonte(fig_fit)
        fig_fit.text(0, 0, "Número de casos dobra em "
                     + str(int(dobro_c))
                     + " dias\nCrescimento em um mês: "
                     + str("{:.2f}").format(cresc_c)
                     + " vezes\n\nNúmero de mortes dobra em "
                     + str(int(dobro_m))
                     + " dias\nCrescimento em um mês: "
                     + str("{:.2f}").format(cresc_m) + " vezes",
                     fontsize=8,
                     horizontalalignment='left',
                     verticalalignment='bottom')
        fig_fit.tight_layout()
        return(fig_fit)

    def graf_fit(self, periodo=0, proj=28):
        print("Gerando projeções")
        if periodo == 0:
            periodos = [7, 14, 21, 28]
        else:
            periodos = [periodo]
        for periodo in periodos:
            print("Projeção dos últimos " + str(periodo) + " dias")
            fig = self.fit(periodo, proj)
            data = max(self.data[-1], self.data_mort[-1])
            nome = self.nome.replace(' ', '_')
            if self.arquivo is None:
                nome += "-SEADE"
            fig.savefig("img/" + data + "-" + nome + "-projecao-" +
                        str(periodo) + "-" + str(proj) + ".png")
            fig.savefig("img/" + nome + "-projecao-" +
                        str(periodo) + "-" + str(proj) + ".png")


def gera_data(dia, referencia, data):
    label = datetime.datetime.strptime(data, "%Y%m%d")
    delta = datetime.timedelta(days=referencia-dia)
    label = datetime.datetime.strftime(label - delta, "%d/%m")
    return(label)


def corrige_y(ax):
    _, max_value = ax.get_ylim()
    max_value = int(math.ceil(math.log(max_value, 10)))
    y_ticks = []
    for i in range(max_value):
        for j in [1, 2, 3, 5]:
            y_ticks.append(j * 10 ** i)
    ax.yaxis.set_major_locator(ticker.FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))


def autolabel(ax, rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 2),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def fig_add_title(fig, title):
    """ Adiciona um título a figura e ajusta o gráfico na janela"""
    fig.gca().set_title(title)
    # fig.tight_layout()  # otherwise the right y-label is slightly clipped


def download_seade():
    """ Obtem dados atualizados do SEADE"""
    url = ("https://raw.githubusercontent.com/seade-R/dados-covid-sp/"
           "master/data/dados_covid_sp.csv")
    response = urllib.request.urlopen(url)
    text = response.read()
    text = str(text, 'utf-8')
    text = csv.DictReader(text.splitlines(), delimiter=';',
                          quoting=csv.QUOTE_NONE)
    return(text)


def plt_seade(cidades):
    for cidade in cidades:
        dados_seade = download_seade()
        print("Processando dados de " + cidade)
        covid = Covid(nome=cidade, dados_seade=dados_seade)
        fig = covid.graf_all()
        fig.savefig("img/" + covid.nome.replace(' ', '_') + "-SEADE.png")
        covid.graf_fit()  # precisa marcar como SEADE no nome do arquivo


if __name__ == '__main__':
    print("Processando dados de Piracicaba.")
    pir = Covid("Piracicaba.txt")
    pir.atualiza_graf(save=True, atualiza_texto=True, show=False)
    pir.graf_detalhes(salva=True, mostra=False)
    pir.graf_fit()
    print("Processando dados de Campinas.")
    camp = Covid("Campinas.txt")
    camp.atualiza_graf(save=True, atualiza_texto=True, show=False)
    camp.graf_detalhes(salva=True, mostra=False)
    camp.graf_fit()
    print("Atualizando dados do SEADE.")
    cidades = ["Campinas", "São Paulo", "Piracicaba", "Limeira",
               "Ribeirão Preto"]
    plt_seade(cidades)
    # teste
    # pir.atualiza_graf(show=True)
