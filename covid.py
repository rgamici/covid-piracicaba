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
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import math
import urllib.request


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
        self.limpa_datas_marcadas()

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
        cidade = self.nome.lower()
        matches = re.findall(cidade + ";.*;", dados_seade)
        for match in matches:
            pattern = (cidade +
                       "; *([0-9NA]+); *([0-9NA]+); *([0-9]+); *([0-9]+)")
            result = re.search(pattern, match)
            if result:
                data = datetime.datetime.strftime(
                    datetime.datetime.strptime(result[3] + " "
                                               + result[4] + " 2020",
                                               "%d %m %Y"), "%Y%m%d")
                datas.append(data)
                conf.append(int(result[1]) - acc_conf)
                acc_conf = int(result[1])
                if result[2] != "NA":
                    morte = int(result[2])
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
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def plot_conf(self, x, y, cor, datas, ylabel, fig=None, add=False):
        """ Plota o número de novos casos

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
        #
        ax.set_ylabel(ylabel, color=cor)
        ax.bar(x, y, color=cor)
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
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        return(fig)

    def marcar_datas(self, fig, x_axis, y_axis, label):
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
                or int(label[i]) % 100 == 1
                or int(label[i]) % 100 == 15
            ):
                x_ticks.append(x_axis[i])
                x_labels.append(label[i][6:] + '/' + label[i][4:6])
                vlines_x.append(x_axis[i])
                vlines_y.append(y_axis[i])
                self.datas_marcadas_i.append(x_axis[i])
                self.datas_marcadas.append(label[i][6:] + '/' + label[i][4:6])
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

    def fig_add_fonte(self, fig,):
        """ Adiciona a fonte dos dados no canto"""
        fig.text(1, 0, self.fonte, fontsize=7, horizontalalignment='right',
                 verticalalignment='bottom')
        fig.tight_layout()  # otherwise the right y-label is slightly clipped

    def graf_conf(self):
        fig_conf = self.plot_conf(self.dias, self.conf, 'tab:blue',
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
        self.plot_conf(self.dias, self.conf, 'tab:blue', self.data,
                       'Novos Casos por Dia', fig_both, True)
        fig_add_title(fig_both, "Casos Confirmados de Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_both)
        return(fig_both)

    def graf_mort(self):
        fig_mort = self.plot_conf(self.dias_mort, self.mortes, 'tab:orange',
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
        self.plot_conf(self.dias_mort, self.mortes, 'tab:blue', self.data_mort,
                       'Novas Mortes por Dia', fig_both_mort, True)
        fig_add_title(fig_both_mort, "Mortes por Coronavírus em "
                      + self.nome)
        self.fig_add_fonte(fig_both_mort)
        return(fig_both_mort)

    def graf_all(self):
        # ### desloca eixo x de mortes
        self.dias_mort_corr = []
        for dia in self.dias_mort:
            self.dias_mort_corr.append(dia + self.diff_morte)
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
        self.plot_conf(self.dias, self.conf, 'tab:blue', self.data,
                       '', fig_all, True)
        self.plot_conf(self.dias_mort_corr, self.mortes, 'tab:orange',
                       self.data_mort,
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
        if self.arquivo:
            sufixo = ""
        else:
            sufixo = "-SEADE"
        if save:
            fig_conf.savefig("img/" + self.data[-1] + "-"
                             + self.nome + '-novoscasos' + sufixo + '.png')
            fig_acc.savefig("img/" + self.data[-1] + "-"
                            + self.nome + '-totalcasos' + sufixo + '.png')
            fig_both.savefig("img/" + self.data[-1] + "-" + self.nome +
                             '-casosconfirmados' + sufixo + '.png')
            fig_mort.savefig("img/" + self.data_mort[-1] + "-" + self.nome
                             + '-novasmortes' + sufixo + '.png')
            fig_acc_mort.savefig("img/" + self.data_mort[-1] + "-" + self.nome
                                 + '-totalmortes' + sufixo + '.png')
            fig_both_mort.savefig("img/" + self.data_mort[-1] + "-"
                                  + self.nome + '-mortes' + sufixo + '.png')
            data = max(self.data[-1], self.data_mort[-1])
            fig_all.savefig("img/" + data + "-" + self.nome + ''
                            + sufixo + '.png')
        if atualiza_texto:
            fig_conf.savefig("img/" + self.nome + '-novoscasos'
                             + sufixo + '.png')
            fig_acc.savefig("img/" + self.nome + '-totalcasos'
                            + sufixo + '.png')
            fig_both.savefig("img/" + self.nome + '-casosconfirmados'
                             + sufixo + '.png')
            fig_mort.savefig("img/" + self.nome + '-novasmortes'
                             + sufixo + '.png')
            fig_acc_mort.savefig("img/" + self.nome + '-totalmortes'
                                 + sufixo + '.png')
            fig_both_mort.savefig("img/" + self.nome + '-mortes'
                                  + sufixo + '.png')
            fig_all.savefig("img/" + self.nome + sufixo + '.png')
        if show:
            plt.show()


def fig_add_title(fig, title):
    """ Adiciona um título a figura e ajusta o gráfico na janela"""
    fig.gca().set_title(title)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped


def download_seade():
    """ Obtem dados atualizados do SEADE"""
    url = ("https://raw.githubusercontent.com/seade-R/dados-covid-sp/"
           "master/data/dados_covid_sp.csv")
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = str(data, 'iso-8859-1')
    return(text)


if __name__ == '__main__':
    pir = Covid("Piracicaba.txt")
    # pir.atualiza_graf(show=True)  # Mostra figuras mas não salva
    # pir.atualiza_graf(save=True)  # Salva figuras com data e não mostra
    # pir.atualiza_graf(atualiza_texto=True)  # Salva figuras sem data
    # pir.atualiza_graf(save=True, atualiza_texto=True, show=False)
    # camp = Covid("Campinas.txt")
    # camp.atualiza_graf(save=True, atualiza_texto=True, show=False)
    dados_seade = download_seade()
    pir_seade = Covid(nome="Piracicaba", dados_seade=dados_seade)
    pir_seade.atualiza_graf(save=True, atualiza_texto=True, show=True)
    # camp_seade = Covid(nome="Campinas", dados_seade=dados_seade)
    # camp_seade.atualiza_graf(show=True, save=True, atualiza_texto=True)
