# COVID-19 em Piracicaba

![conf](img/Piracicaba.png)

## Dados

Os dados referentes ao número de casos confirmados, o de mortes, e as informações sobre cada paciente são obtidas do [site da Prefeitura de Piracicaba](piracicaba.sp.gov.br/).
Embora não haja nenhuma página organizando os dados, eles podem ser extraídos da página com [notícias sobre o coronavírus na cidade](http://www.piracicaba.sp.gov.br/plantao+coronavirus+covid+19.aspx), ou nas [notícias em geral](https://www.piracicaba.sp.gov.br/categoria/principais+noticias.aspx) (com o título "COMUNICADO ...").

Os dados extraídos são colocados em um arquivo com a seguinte formatação  
`Data   Tipo   Número   Sexo   Idade  ## Observação`

O campo `Tipo` é usado para marcar casos confirmados (`P`) ou óbitos (`M`).
Quando não há informações sobre o paciente, os campos `Sexo` e `Idade` são marcados com `--`.

## Gráficos

Para atualizar os gráficos, basta rodar o script `covid.py` e os arquivos na pasta `img` serão modificados para incluir os dados mais recentes.
Se quiser apenas vê-los, descomente o comando `# pir.atualiza_graf(show=True)  # Mostra figuras mas não salva` no fim do arquivo.

São gerados os seguintes gráficos:
* Novos casos confirmados por dia (`novoscasos`)
* Total de casos confirmados (`totalcasos`)
* Mortes por dias (`novasmortes`)
* Total de mortes (`totalmortes`)
* Combinação dos novos casos por dia e do total de casos (`casosconfirmados`)
* Combinação das mortes por dia e do total de mortes (`mortes`)
* Combinação de todos os 4 tipos de dados (arquivo sem sufixo)
