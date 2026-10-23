**Revisando KPIs e métricas para Projeção de consumo de
amostras-20261021_130113-Meeting Recording**

October 21, 2026, 4:01PM

1h 10m 18s

**Caio Alcantara** started transcription

**Rafael Roriz** 0:04  
It's okay, I'll say report. Uh, eu acho que so.

**Caio Alcantara** 0:06  
Acho que alguém faz com um background aí fazendo um barulho aí.

**Rafael Roriz** 0:15  
Acho que sou eu, não sei, é porque eu estou aqui no escritório.

**Caio Alcantara** 0:21  
Other.  
Bom, eu vou compartilhar minha tela então pra gente poder começar.
Preparei uma apresentação para trazer para vocês, mas basicamente
apresentar para vocês o Rafael, ele vai ser o cientista de dados que vai
estar acompanhando a gente no projeto de forecast que a gente vai estar
trabalhando. Esse vai ser os primeiros que a gente vai iniciar, que
foram os de mais impactos que a gente identificou.

**Rafael Roriz** 0:34  
I'm not it.  
So.  
I'm just saying that.

**Caio Alcantara** 0:42  
E é basicamente o porquê que a gente está fazendo essa reunião. É porque
devido a esses podcast que a gente identificou no decorrer das reuniões
que a gente teve referentes aos outros, é, eu queria.

**Rafael Roriz** 0:45  
Go from unifying the party.  
I.  
Okay.

**Caio Alcantara** 0:57  
Rafael, eu acho que você vai poder deixar no mudo, aí quando você for
falar alguma coisa, você tira porque tá.  
Bom, basicamente, no decorrer das reuniões que a gente teve, quando a
gente estava trabalhando, falando sobre o Zoom, identificando quais KPIs
a gente iria trabalhar, a gente teve diversas informações, então eu uni
todas essas informações juntas e preparei essa apresentação para a gente
validar.  
Se a nossa linha de raciocínio está correta, se a gente está seguindo um
raciocínio apropriado para a gente de fato ter uma validação correta e
seguir o Rafael conseguir seguir com os dados corretos para a gente
trazer uma métrica coerente, certo?  
Bom, as duas métricas que a gente vai estar trabalhando são forecast de
consumo de amostras. Então, quanto cada cliente vai gerar de amostra com
base no consumo dos equipamentos e o forecast de vendas, que seria a
previsão de faturamento.  
A gente tem aqui até um ponto que a Kelly tinha mencionado também, eu
acho que até o Bahia também, mas aqui especificamente referente ao
consumo de amostras, que a gente tem duas visões do mesmo cliente,
porque a gente tem a real, que são quantas amostras o cliente deve gerar
com base no histórico dele.  
de fato, e o potencial, que quanto esse cliente poderia gerar baseado no
que a gente tem de outros clientes similares. Então, por exemplo, esse
cliente faz 200 amostras por mês, mas clientes parecidos fazem 400.
Então a gente teria essa diferença entre o real e o potencial.  
Cert.  
É dentro do consumo de amostras. A gente vai estar considerando essas
métricas para fazer o forecast. A gente vai considerar a previsão
real.  
Então as horas trabalhadas, intervalo de coleta por compartimento, por
tipo de equipamento, segmento que com base na calculadora de que foi o
compartilhado comigo, acho que pelo Bahia.  
Certo é o potencial que foi os são os equipamentos cadastrados versus
monitorados e benchmark de clientes semelhantes também que entra na
questão do da previsão.  
A porcentagem de atingido, que são a quantidade de amostras realizadas
dividido pelo potencial anual do cliente, sinais de ação, queda acima de
20% nas amostras ou algum compartimento que deixou de coletar.  
E também considerar a sazonalidade, os meses trabalhados por ano, porque
cada segmento tem um tipo específico de funcionalidade dependendo da
época do ano, certo?  
E como a receita é estimada, ela vai ser composta. A gente tem a receita
recorrente, que são os clientes com o padrão regular de compra. A gente
tem anão recorrente ativa, que são os clientes que compram poucas vezes,
mas tem 1 o volume alto.  
A gente tem novos clientes, valor médio do primeiro faturamento, os
reativados e aí aqui todas essas são positivas E aí a gente tem o churn
e a variável de mercado que são as que de fato podem subtrair ou
deixar  
equivalente né É até o momento tem algum ponto porque assim se tiver
alguma coisa para pontuar vocês podem ir me trazendo durante porque aí
eu vou ajustando depois e o Rafael também se tiver

**Diego Souza** 4:20  
Da minha parte aqui, Caio, tá tranquilo, vai muito do que você tinha
aquele material que a gente te mandei lá da Kelly, não sei se te ajudou
a ter uma ideia, né? Então até aqui tá tranquilo, tá?

**Caio Alcantara** 4:24  
With the certain.  
Mhm.

**Ederson Bahia** 4:34  
Tá aqui também, Caio, faz muito sentido aquilo que você já pontuou no
slide anterior, do segmento de clientes de atuação, isso tudo interfere,
tá? Então é importante seguir esse fluxo, porque é o mesmo equipamento
em segmentos diferentes que eu tenho.  
realidades completamente diferentes. Só uma pergunta, já que a gente
está nessa tela. Tem ali na primeira receita recorrente, clientes com
padrão regular de compra. Existem clientes que não têm esse padrão
regular?

**Caio Alcantara** 4:57  
Mm.

**Ederson Bahia** 5:05  
Tá, é a linha de baixo. Ele compra poucas vezes e volume muito alto. Ele
compra uma vez por ano e compra tudo de uma vez. Olha só, é isso. Você
está considerando nessa segunda linha aí.

**Caio Alcantara** 5:17  
Tem um padrão que inclusive a Kelly tinha definido, que foi justamente
esse aqui, que no caso são os clientes que comprou dentro dos últimos 6
meses, comprou em 6 mais meses, diferente dos últimos 12.

**Ederson Bahia** 5:21  
Tá ótimo.

**Caio Alcantara** 5:32  
ou então a última compra a menos de 90 dias é no caso esse vai ser
considerado um recorrente no caso nesse caso

**Ederson Bahia** 5:39  
Perfect, I say Mendel's to to creation a half, that's it.

**Caio Alcantara** 5:43  
Eu acho que nesse caso que você mencionou, se for um cliente, por
exemplo, que compra uma vez no ano um alto volume, eu acho que ele seria
não recorrente ativo.

**Diego Souza** 5:50  
É isso mesmo, porque ele fica consumindo aquele valor alto que ele
comprou em análise. Ele está processando normal, ele processa, ele não
compra, mas ele processa. Então ele é um recorrente, não é não
recorrente ativo, ou bom termo usado.

**Caio Alcantara** 6:00  
Mhm.

**Ederson Bahia** 6:04  
Okay.

**Diego Souza** 6:05  
A legal is say.

**Caio Alcantara** 6:07  
Perfeito. Pode falar Rafael.

**Diego Souza** 6:08  
No.

**Rafael Roriz** 6:11  
É com licença, é primeiramente prazer. Aí eu já tinha, já conhecia, já
tinha visto o Diego, o Bahia, não tinha visto aí prazer. Sou Rafael, sou
um cientista de dados aí que eu ia trabalhar com vocês.  
E um padrão de não recorrente ativo é um padrão já bem estudado nas
séries temporais, né? Fico feliz, inclusive, que seja algo relacionado à
receita.

**Ederson Bahia** 6:26  
Seja muito bem-vindo!

**Rafael Roriz** 6:43  
Porque nós temos modelos de reconhecimento, padrão de receita já muito
bem estudados, como os modelos que eu trabalho aqui para outra outro
tipo de abordagem. Eu trabalho com engenharia, mas eu uso, eu utilizo
modelos.  
Que são utilizados para receita, né? Que é principalmente o modelo de
mudança de ponto de segmento, né? O changepoint, que é um modelo de
programação dinâmica, que ele é feito para poder trabalhar em séries
temporais, principalmente bancárias e de receita, né?  
Ele foi feito para bancos, então trabalhar com receita é algo já bem
usual nos modelos de preditivos. Então isso aí, esse tipo de padrão, não
é facilmente reconhecível, mas dá para reconhecer muito bem assim, dá
para fazer boas predições com

**Ederson Bahia** 7:25  
Okay, option.

**Rafael Roriz** 7:35  
Acurácia ali bem, é eficiência boa assim de mercado, que nós possamos
trabalhar bem, entendeu?  
And, so is this Miss Banka Tamaki?  
A apresentação tá boa aí.

**Caio Alcantara** 7:51  
Bacana qualquer coisa também. Se tiver alguma dúvida, Rafael, você pode
falar aqui no meio do processo também, que é bom que com os meninos já
estando aqui, é bom que você já vai ter uma resposta bem tipo direto do
departamento mesmo também, qualquer coisa.  
Bom, aí aqui no caso entra a explicação do que significa o que define
uma receita recorrente, que são o que a gente tinha passado aquela hora
e aqui também tem um ponto que foi o que a Kelly tinha mencionado
recentemente, que.  
É seria referente a essa taxa de conversão de 70% porque ela mencionou
que ela tinha recentemente tirado essa taxa de conversão porque não
fazia sentido, já que ela estava considerando as vendas faturadas e não
o orçamento vezes fechado de fato.

**Diego Souza** 8:35  
perfeito pode manter pode manter vou te explicar porque eu ainda eu
estou olhando receita aqui se eu for misturar conversão com receita Às
vezes o meu nome pode ficar furado porque eu vou te falar assim olha eu
tive 100

**Caio Alcantara** 8:36  
I.E. I've said.

**Diego Souza** 8:51  
É orçamentos, mas fechei 2, mas só que esses 2 que eu fechei são valores
altos. Eu tive uma receita que não veio diretamente da conversão. Foi de
um trabalho fora da curva que o cara atingiu um número de 500000 fazendo
2 conversões.  
E aí se eu for puxar o histórico dele, a conversão dele é péssima, mas a
receita dele é boa. E eu tenho casos aqui onde eu faço várias vendas
menores, bato meta, mas também eu faço poucas vendas e também bato
meta.  
Então, acho que  
Colocar a conversão aqui nesse acho que ela puxa um pouco fora, tá? Acho
que é bom a gente manter essa taxa de conversão por enquanto fora.
Quando eu for olhar a efetividade de funil ou de é.  
oportunidade aí sim eu falaria com conversão aí beleza tá

**Caio Alcantara** 9:47  
Então, perfeito. Então você acha que faz sentido a lógica da Kelly de
manter sem a taxa de conversão?

**Diego Souza** 9:53  
Faz sentido, faz sentido manter. Fala Rafael,

**Caio Alcantara** 9:54  
Perfect, perfect.

**Rafael Roriz** 9:56  
É, até porque eles são KP diferentes e são relacionáveis. Eles servem
para poder fazer diferentes tipos de predição. Então, se nós
relacionarmos ela, dá para trabalhar outros tipos de predição, né?  
Prever outros números, criar outras outros campos de tabela, enfim, são
tratados diferentes ou dados tratados de maneira diferente nas regras de
negócio.

**Caio Alcantara** 10:25  
Centre Centre.  
Bom, então aqui a gente fala especificamente sobre o consumo e venda,
porque hoje o forecast olha apenas as vendas e a visão por amostras
acaba que ainda não entra, mas com o projeto a gente vai medir a
correlação entre eles, a gente vai usar todas essas métricas de definir
tipo pesos entre elas.  
pra gente chegar numa velocidade melhor.  
E essas daqui são as nossas fontes que a gente vai utilizar de dados. A
gente vai usar o nosso US 360, o Proteus e também a gente vai usar como
base as planilhas que vocês compartilharam no decorrer das reuniões que
a gente teve.  
Essas daqui são de fato as planilhas que vocês compartilharam com a
gente. Então a gente tem a calculadora de amostras que o Bahia
compartilhou comigo. A gente tem esse Costomer Status, que seria
referente aos dados dos clientes com o  
O cruzamento já mostra equipamento.  
Certo? E o de forecast também, com a receita mensal, mas recorrente, não
recorrente, novos e ativados, churn.  
Certo? E essas daqui são alguns pontos que eu só queria confirmar se a
calculadora, se tem alguma coisa a ser atualizada, se está tudo certo e
se o forecast também, se está tudo certo. E essa daqui também o Diego já
confirmou que seria referente a regra de remoção do 70% que a gente já  
validou e por último entender sobre o como que esse ano ou sample
potential tá sendo gerado hoje em dia né porque eu acho que no decorrer
das reuniões acabou que foi algo que ficou um pouco lá

**Diego Souza** 12:08  
Você teve acesso à planilha que a Kelly te mandou, a gente chama de
planilhão, ela te mandou esse planilhão, não é?  
A Rafael está rindo que eu acho que ele é um planilhão com vários
clientes lá, com todas as vendas.

**Caio Alcantara** 12:17  
Okay.

**Rafael Roriz** 12:23  
Eu trabalho na engenharia, no governo, eu trabalho não terceirizado,
então eu sei, eu conheço bem essa esse termo, banilhão.

**Diego Souza** 12:31  
Vamos planilha, deixa eu te mostrar ele para ver se foi esse que ela te
encaminhou, tá? Deixa eu te mostrar que eu acho que é esse, mas vamos
confirmar, tá? Porque se você me falasse, não, pô Diego, é esse aí
mesmo, cara, é esse aí mesmo. E a gente vai tentar responder essa que
está em aberto para você. Deixa eu só compartilhar.  
esse é esse aqui ó só vou pingar minha tela aqui rapidinho tá o Caio só
um minutinho

**Caio Alcantara** 12:53  
Tá tranquilo.

**Diego Souza** 12:56  
This is a here, this.

**Caio Alcantara** 12:59  
Deixa eu só validar aqui um minuto.  
É como que é o nome desse customer status?

**Diego Souza** 13:06  
Novas carteiras.  
porque aqui ó eu acho que é esse aqui mesmo tá vendo onde eu vou pintar
de amarelo aqui ó aqui ó

**Caio Alcantara** 13:10  
Hello, it's very sure.

**Diego Souza** 13:18  
Bahia, você é o cara que ajudou a criar esse ano ao sempre sem pull
potential. Ah lá ele tá rindo pô para de rir tá ele é o responsável por
criar isso aqui então ele é o melhor cara

**Ederson Bahia** 13:28  
Okay.

**Diego Souza** 13:33  
para responder essa pergunta porque ele é uma um cruzamento de vários
dados de equipamentos perfil e aí a gente chegou no número que por
exemplo eu falo que esse cliente tem um perfil de fazer 665 amostras  
Se ele não faz, por que ele não faz, entendeu?  
Então deixa eu te compartilhar então essa planilha mesmo, Caio?

**Caio Alcantara** 13:59  
Aadi Aadi Aadi Aadi

**Diego Souza** 14:01  
Então pode voltar, aí a gente vai discutir.

**Caio Alcantara** 14:04  
Tá certo, é isso mesmo.

**Ederson Bahia** 14:04  
Tá bom, a planilha, ela basicamente faz a conta daquilo que nós
conversamos em algumas reuniões e você colocou já na apresentação. Eu
vou verificar segmento de cliente, eu vou verificar o perfil do cliente,
eu vou verificar o tipo de equipamento que ele tem.  
E aí eu faço uma previsão do que ele poderia gerar de amostras, do que
ele faz um comparativo de outros crises. Então tudo que é basicamente é
OA lógica dessa planilha é o que a gente descreveu aqui para você, tá?  
É a planilha, ela funciona, mas ela é muito pesada, é difícil de mexer e
ela não tira insights que a gente vai conseguir agora com uma ferramenta
muito melhor. Então ela dá um número, mas ainda mais estático e um ou
outro e acaba tendo um erro porque.  
Você vai fazendo as fórmulas, então alguma forma ele pode pegar ali
algum dado que naquele momento pode não ser o mais assertivo ou mais
próximo na realidade e gerar um número lá na frente e ficar correndo
atrás desse número de forma enganada. Mas basicamente é isso mesmo. Eu
verifico segmento, verifico família, perfil de cliente.  
Pontos de coleta, olhe dentro de 60 os equipamentos que estão
cadastrados, pontos de coleta cadastrados e valendo essas informações e
gera depois esses percentuais. Sobre a calculadora que está na tela, ela
é aquilo mesmo. Ela não teve uma evolução porque ela reflete muito.  
A identidade do equipamento. O equipamento não muda, então eu tenho
sempre aquele mesmo equipamento com aqueles pontos de coleta de novo.
Desculpa ser repetitivo, mas o que vai mudar é o segmento do cliente, o
perfil do cliente. Essa calculadora.  
É, nós quando fizemos, nós não colocamos todas as famílias de
equipamentos. Se eu for pegar todas as famílias de equipamentos no 360,
eu vou estar falando aí de olha, eu vou chutar, mas eu estou. Eu acho
que é mais de 400 famílias.  
Tá? É um número muito grande, então nós pegamos as principais, a que
faria mais sentido, porque a ideia era a gente fazer uma consulta rápida
e conseguir entender sobre aquele cliente, quantas amostras eu iria
ofertar para ele ou não.  
Então Rafael pode ser que na hora que você começa a trabalhar nessa
planilha você vai trabalhar com os principais mas você pode identificar
um determinado equipamento para Bahia. Esse equipamento aqui tem 1 o
volume considerado de amostras. Aí você me chama, a gente desenha o
cenário dele e segue sem problema nenhum.  
That.

**Rafael Roriz** 16:36  
Com licença, eu já tenho algumas dúvidas aqui, é principalmente em
relação ao Ana Paula Sample Potential, que é sobre a planilha primeiro,
né? Essa planilha, ela é uma macro, né? Ela é uma.  
Um BB, é uma XLSM, é uma macro ou ela é feita por fórmulas?

**Ederson Bahia** 17:01  
Bom, quando eu fiz ela, já tem um tempo, eu fiz ela por fórmulas e
depois disso a Kelly melhorou essa planilha. Então ela pode ter mudado a
estrutura dela. Eu fiz ela como o Diego falou, foi lá atrás, eu estou
falando isso aí de 2021/2022.

**Rafael Roriz** 17:10  
Okay.  
Mhm.  
It's.

**Ederson Bahia** 17:17  
Então ela já mexeu e já melhorou ela, então pode ser que ela tenha
mudado a estrutura.

**Rafael Roriz** 17:19  
Here, Pedro.  
Depois gostaria de olhar aí para ver como é feito o cálculo. É as
fórmulas, são fórmulas de.  
É a fórmula de predição é uma regressão.

**Ederson Bahia** 17:37  
Não, não são formas que eu apliquei nos dados existentes, tá? Eu não
cheguei a fazer regressão, não.

**Rafael Roriz** 17:48  
Entendi. Agora sobre a calculadora.  
A calculadora, pelo visto, ela é essa pergunta de que os parâmetros
ainda valem e os parâmetros ainda valem, só que existem outros
parâmetros que valem agora. Seria isso a ser alterado?

**Ederson Bahia** 18:09  
Na verdade, eu não sei ao certo, mas entenda que eu tenho nessa
calculadora, sei lá, 20, 30 principais famílias de equipamentos já
mapeadas. Isso aí imagino eu que deva estar, senão 80/20 perto disso.  
Tá bom? E aí você vai ter outras famílias de equipamentos que não estão
mapeadas e aí se você perceber que alguma família tem uma quantidade
representativa de amostras ou uma quantidade representativa dentro dos
clientes, aí a gente vai trabalhar ela. Mas é simples, é só entender que
família é

**Rafael Roriz** 18:25  
Perto disso.  
Okay.

**Ederson Bahia** 18:44  
Seguimento e os pontos de coleta. Isso é uma coisa tranquila de ser
feita, tá? Nós não fizemos na época que eu não tinha essa necessidade.

**Caio Alcantara** 18:45  
O.

**Rafael Roriz** 18:47  
Okay.  
Okay.

**Diego Souza** 18:53  
Você teve acesso a calculadora, Rafael?

**Rafael Roriz** 18:53  
É, eu não. Eu não olhei no Fabio, mas eu tive acesso. É a documentação
que o Carlos me enviou. Falava sobre essa calculadora com um certo.  
Detalhe, entendeu? E.

**Diego Souza** 19:09  
O Caio, você teve access Caio também?

**Caio Alcantara** 19:12  
Thing.

**Diego Souza** 19:13  
Legal, Rafael, uma calculadora que ela vai abranger, como falou, 80% do
nosso negócio. É porque tem particularidade de equipamentos novos de
2022 para cá que podem ter sido criados por algum outro cliente, um
cliente.

**Rafael Roriz** 19:21  
Mm.  
Yeah.

**Diego Souza** 19:29  
Pô, é uma escavadora. Aí o cara coloca assim, escavadora autônoma, pô.

**Rafael Roriz** 19:32  
Santos.

**Diego Souza** 19:35  
É um equipamento novo, mas que também tem um conjunto de motor, tá? Só
que aí a gente precisa filtrar esses fora da curva.

**Rafael Roriz** 19:41  
também então

**Diego Souza** 19:48  
Uma pesquisa e aí mapear realmente é o esse novo, essa nova família, mas
a maioria a gente já tem, já tá dando certo, tá?

**Rafael Roriz** 20:02  
Então é isso aí e sobre o forecast o forecast né que já existe ele tá
dentro do panilhão ele tá lá no febre que tá dentro do Power BI é feito
em Data

**Diego Souza** 20:15  
É esse forecast, ele é feito no BI que a gente tem. Você teve acesso a
ele funcionando?

**Caio Alcantara** 20:24  
Centre Power BI.

**Diego Souza** 20:26  
Isso aquele Power BI que a gente tem, que tem o forecast.

**Caio Alcantara** 20:32  
Não, eu acho que o Power BI eu não tenho acesso, na verdade.

**Rafael Roriz** 20:33  
Okay.

**Diego Souza** 20:34  
Posso mostrar aqui para vocês ou não?

**Caio Alcantara** 20:36  
Pode compartilhar.

**Diego Souza** 20:38  
Deixa eu pegar aqui, deixa eu só.  
Fechar um pouco de janela aqui, porque senão, pô, vocês não enxerga
nada.  
Então eu tenho aqui, é.  
Então eu tenho aqui o nosso BI.  
Então aqui para o mês de outubro ele vai fazer o cálculo, não sei se
vocês estão enxergando aí, tá?  
Então ele já me passa a receita, isso é atualizado de hora em hora. A
última atualização foi agora 1 hora, tá? Então ele me fala que eu já
tenho 3 e 45 de receita. Oi, Kelly, tudo bom? Bom dia, boa tarde.

**Keli Ordoz** 21:23  
Olá Gustavo, boa tarde, tudo bem?

**Caio Alcantara** 21:24  
Boa tarde, Kelly.

**Rafael Roriz** 21:26  
Oi Kelly, boa tarde, prazer.

**Ederson Bahia** 21:26  
Keli Keli Jim.

**Diego Souza** 21:26  
Tudo bem?  
bom então aqui eu tenho é uma receita ela chegou bem na hora três horas
é 3 milhões e 45 e 45 né nossa receita atual aí que que acontece ele vai
fazer um cálculo do que ele vai pegar e é

**Keli Ordoz** 21:29  
Sear.

**Diego Souza** 21:45  
Empresas que tem uma receita recorrente, aí entra aquele ponto que a
gente estava comentando. Ele vai falar para mim, falou, olha, a
automogiana sempre compra 33 mil reais todo mês, tá? Só que ele não está
mapeado como oportunidade ainda.  
ele compra Então vai cair é um recorrente ele vai vir esse esse esse
essa oportunidade então é a gente poderia usar esses clientes que ele
aponta como recorrentes mensais para criar oportunidade dentro dele fora
isso ele mostra também  
Que temos também negociações em andamento, por exemplo, Eldorado,
sistema MG, lavronorte, que são negociações já acima de 80%. É aquela
negociação que o vendedor fala, pô, essa aí tá na boca do Golpo, é só
empurrar.  
E já está tudo pronto. Então ele fala aqui, que é o as oportunidades
mais altas, o top 5. Então ele faz essa inteligência olhando as
oportunidades acima de 80% mais as recorrentes e me dá o número 4.8
milhões. Ou seja.  
Se eu somar o que eu já vendi com o que eu tenho para entrar, ele me
aponta um Horizonte de previsão que aí resume a conversa, resume o
projeto, é de falar para a minha diretoria, olha, hoje a gente está
apontando para 4.8.  
Minha meta é 5.05. Eu estou fora, entendeu? Eu estou. Eu ainda preciso
correr atrás. Eu preciso correr atrás de 461000 BR\$ de Power Cash para
poder bater a meta, entendeu?  
É isso que Kelly falei, certo? Você que criou a ferramenta, você Bahia
aí?

**Keli Ordoz** 23:26  
Certinho, certinho. É, na verdade, eu acho que até mandei essa o escopo
da regra. Se você for ali, é do lado esquerdo, Diego, forecast rules.

**Diego Souza** 23:37  
Eu mandei para o Caio isso aqui, tá?

**Keli Ordoz** 23:40  
É, deixa eu mandar para ele. É basicamente o caminho que a gente segue,
a lógica que a gente segue para fazer o forecast de receita, né? Então a
gente aponta, primeiro faz essa seleção de quem que seria esse cliente
elegível.

**Diego Souza** 23:42  
Okay.

**Keli Ordoz** 23:57  
o que seria considerado recorrente hoje, né? E assim, reforço que isso
é, nós iniciamos essa medida este ano, né? Então pode ser que, por
exemplo, a gente vem acompanhando esse número  
Nos últimos meses ele vem chegando bem próximo, né, Diego, assim, do que
a gente está fazendo mesmo. Mas é uma coisa muito dinâmica, né? Então
assim, pode ser que ano que vem o Diego tenha um outro pensamento, ele
vai falar assim, olha aqui.

**Diego Souza** 24:17  
That.

**Keli Ordoz** 24:29  
Recorrente para nós não é. Não são mais esses parâmetros aqui. Hoje os
parâmetros são esses que a gente encara como um cliente recorrente. É
recorrente.  
Em faturamento, recorrente em amostras é bem diferente, né Bahia? Então,
assim, acho que são duas visões que se complementam muito. Então, uma
coisa a gente olhar o comportamento desse cliente em termos de
faturamento.  
E outra coisa é a gente olhar o comportamento de recorrência dele de
amostras, até porque a gente tem muita coisa assim, por exemplo, que é
muito difícil da gente identificar. Por exemplo, a gente tem um cliente
número, o cliente número 1.

**Diego Souza** 25:04  
Quick.

**Keli Ordoz** 25:15  
Ele compra para várias unidades, então, tipo, quando a gente vai fazer o
apontamento lá na compra, sempre vai aparecer ele, porque ele tem um
histórico que compra. Mas na hora das amostras, talvez aquele código
dele não processa nenhuma amostra.  
Porque ele compra e ele distribui para as outras unidades ou para os
concessionários. E aí são esses concessionários que não possuem
faturamento, mas eles geram demanda de amostras. Então, aí a importância
da gente entender.  
O comportamento de recorrência de amostras e juntar.

**Diego Souza** 25:50  
E aí, e aí vai muito, Milani entrou e saiu da reunião, entrou e saiu. Aí
que vai entrar, Rafael e Caio, o que a gente precisa para o negócio.
Vocês estão entendendo agora? O Caio já está aqui um pouco mais de
tempo, ele já está entendendo o negócio como funciona.

**Keli Ordoz** 25:54  
Okay.

**Diego Souza** 26:10  
Eu sou a vocês, por exemplo, vão na academia, compra o whey protein, vai
comprar lá, tem que tomar todo dia, não tem que tomar todo dia. Aí o que
acontece, se você não toma todo dia, a Growth lá que vende o whey
protein vai te começar a te bombardear de assunto assim.  
Pô, você tem que tomar todo dia de manhã e à noite, porque ela quer que
você consuma para você fazer uma nova recompra. E aí é o que o nosso
caso. A gente precisa que o cliente siga o plano da máquina dele para
fazer uma nova recompra.  
E essa recompra gera venda, venda, recorrência, recorrência gera receita
recorrente e a gente mantém o sistema rodando. Então essa estratégia
aqui é eu entender a projeção de consumo de amostra e quanto que essa
representação desse consumo.  
representa em receita para nós tá então é são duas a gente pode chegar
num consenso que a gente vai ter uma receita assim de forecast boa
recorrente e baseada no consumo que seria o ideal que hoje infelizmente
né que a gente não consegue ainda  
Mensurar 100% é esse número.

**Keli Ordoz** 27:17  
É, hoje a parte de a gente fazer esse forecast de amostra é bem, bem
complexo, a gente não tem, assim, a gente não tem esse número, então não
tem nada para apresentar para vocês, falar assim, olha, tem isso aqui,
meio capenga.  
Você dá uma melhorada, não forecast de avós, nós vamos outro plano de
nível Bahia, talvez você tenha, estou falando de verdade, você tem sim,
gente, retira o que eu disse, o Bahia tinha, ele tinha sim forecast de
avós, de repente.

**Diego Souza** 27:41  
Ele fez aquele anual lá, sim, pô, a gente estava conversando, é?

**Keli Ordoz** 27:50  
Pode ser um escopo para eles é terem uma ideia, não é?

**Diego Souza** 27:52  
Mas a gente já conversou aqui na é, a gente já conversou aqui na reunião
agora há pouco.

**Ederson Bahia** 27:54  
Mas fique tranquila, Keli. O Rafael Caio é justamente isso que acontece.
Eu tenho 2 cenários completamente diferentes, a turma de venda do que eu
estou faturando e aí eu tenho muito a Keli e o Diego. E na hora que eu
falo de amostras processadas, então eu trabalho mais com essa parte de
amostras processadas. Então.  
Eu tenho uma previsibilidade de amostras que a gente vai receber no
laboratório até o final do ano, por exemplo. É uma outra planilha, é um
outro outro, e lá assim eu consigo ter um número aproximado e isso ajuda
muito o pessoal interno de processo a entender com relação às amostras
que eu estou recebendo.  
Fazer algum tipo de investimento em equipamento, em pessoas. Se está
chegando a morte, a gente consegue realmente processar e entregar dentro
do prazo programado. Então é uma informação que a gente usa muito de
forma interna, tá? É claro que o pessoal Diego e Kelly precisa de algum
momento desse número.  
Mas é um número mais para o processo interno entender o que está
chegando de amostra, se esse volume está crescendo ou não, do que
propriamente dito. E aí o que a gente quer e a gente gostaria era muito
de cruzar esses dois números e entender sobre o que eu estou
processando, entender sobre o que eu estou vendendo.  
Num passado, aí um passado mais distante, tá, tô falando lá em 2018,
2019, eu fazia um trabalho aonde eu tinha um número que era em torno de
70% tudo que nós vendíamos.  
Eu recebia 70% e processava, outros 30% não era processado, tá? Ficava
no meio do caminho. As pessoas perdiam aquele kit. Não sei se você já
viu o nosso kit, a embalagenzinha de plástico, que vinha um potinho como
a mangueira. Então as pessoas compram esse kit, coletam o óleo e mandam
pra gente. Então.  
Tudo que a gente vendia só retornava a 70. Eu não sei se esse número
hoje ainda é real, se ele continua nessa proporção ou não. Ele tem
trabalhado para aumentar esse número. Imagino que ele tenha crescido,
mas certamente, se eu fosse chutar um número, eu falaria que está em
torno de 80. Não acho que passa disso não.  
Eu acho que esse projeto vai ajudar muito a gente a entender isso
também.

**Caio Alcantara** 30:06  
Costco.

**Rafael Roriz** 30:07  
É uma algo que falta assim, para mim realmente entende o que vai faltar,
realmente entendimento do negócio. Vai demorar um pouquinho aí, umas
semaninhas para eu poder entender como é que funciona esse negócio da
amostra de voltar e tal.  
Mas eu normalmente eu pego rápido porque eu tenho um certo interesse. Já
fiquei interessado assim nesse mercado que eu tenho interesse de saber
dos nichos. Então é muito interessante. Vou pesquisar, perguntar aí para
vocês e perguntando para o Caio, que já está há mais tempo aqui.  
Enfim, em relação a como é que é feita a amostra e ver essa correlação
em relação as métricas de cliente, já estou pensando na classificação do
cliente, porque parece que existem regras de classificação do cliente.  
Só que é, talvez falte uma acurácia maior em relação a saber o que é um
cliente recorrente x, um recorrente mesmo.  
Um recorrente de menor atividade, de mais tempo, o que que é cada
cliente, como eles se comportam para poder fazer um forecast com maior
acurácia, né?  
Então é primeiro um problema de classificação do cliente, depois um
problema de predição, de regressão, de receita e faturamento e de
recorrência também, que parece ser uma KPI também rastreável aí.  
É por já ter regras no BI, por exemplo.  
É interessante pensar já no modelo de regressão de um modelo de
floresta, um modelo que use árvores, porque parece uma árvore já bem
organizada.  
E por enquanto, é isso mesmo que eu tenho para dizer. Vou querer, vou
perguntar mais para vocês e pesquisar também sozinho sobre como é que
funciona esse retorno das amostras e qual a importância e qual a
correlação, né?  
pensar na correlação com o operacional, porque a amostra é a parte
operacional, pelo que eu estou entendendo aqui, e a parte financeira é a
parte dessas outras KPIs, que é as métricas de faturamento,  
É de previsibilidade, é do cliente, enfim, né? Se tiver algum, tiver
alguma coisa, se eu tiver com um pensamento diferente aí do que vocês
estão falando, podem me falar também isso.

**Caio Alcantara** 32:49  
Eu posso, tem muitas reuniões que eu peguei com o pessoal Rafael e aí
tipo assim eu posso até preparar tipo um fluxo mais ou menos assim do
que que eu já tenho com a documentação para você entender um pouco
melhor mas também se surgir a necessidade de dúvidas pontuais a gente
vai marcando reunião para a gente entender mais sobre o negócio também.

**Diego Souza** 33:04  
Não, e a gente está à disposição, Caio. A gente vai parar e explicar
para você, para o Rafael. O Diego, me tira a dúvida como é o fluxo das
análises, como que entra. O Bahia também pode explicar, cara, vocês são
parceiros nossos. A gente quer que vocês nos ajudem.

**Caio Alcantara** 33:06  
Sim.

**Diego Souza** 33:23  
Tá bom, tá? Tem caminho livre aqui para vocês.

**Caio Alcantara** 33:27  
Em relação ao que você mencionou dos clientes que são recorrentes, aqui
a gente tem a definição que no caso seria, por exemplo, se ele comprou
em mais de 6 meses dentro dos últimos 12 e a última compra foi a menos
de 90 dias, aí ele é considerado um  
Cliente de receita recorrente. E aí foi igual os meninos tinham falado
também, que às vezes tem um cliente que compra tipo uma vez no ano, só
que com 1 o volume alto. Aí no caso ele é um cliente de não recorrente
ativo, que ele compra em alto volume, mas ele compra poucas vezes.  
I don't say see there is there is a distribution.

**Rafael Roriz** 34:07  
Não é no caso, já não é. Não é uma dúvida. No caso, é uma sugestão de
fazer um modelo para a classificação dos clientes, entendeu? Fazer a
classificação.

**Caio Alcantara** 34:19  
Fala assim, entendi.

**Rafael Roriz** 34:22  
Those clients in.

**Diego Souza** 34:23  
A gente tem a classificação pelo pela quantidade de equipamentos hoje,
não é, Kelly? Acho que é por equipamentos que a gente faz a
classificação.

**Keli Ordoz** 34:31  
É, na verdade Diego, esse assunto da classificação é que está parado faz
meses, né? A gente tinha uma classificação que foi feita pelo Samuel na
época. Essa classificação, ela unia muitas informações, ela pegava  
Uma janela de 12 meses a gente colocava qual é a média que o cliente
comprou em 12 meses?

**Rafael Roriz** 34:52  
O.  
Okay.  
That.

**Keli Ordoz** 34:58  
Depois a gente olhava um potencial desse cliente que a gente fazia
cálculo que era baseado na quantidade de equipamentos que ele tinha, e
aí se calculava mais ou menos o potencial pela média e tal. Então ele
eram 2 réguas, né? Então ele.  
Olha, ele tem que atingir pelo menos tantos mil por ano, é o que ele
executou e ele tem esse potencial de executar muito mais ou menos ou
tal. E aí a gente fez uma classificação na época, baseado  
mas essa classificação hoje não está mais ativa na verdade desde quando
antes na verdade do Samuel mudar né a divisão dele a gente já falava que
tinha que ser atualizado essa  
Essas regras. E aí a gente já teve várias outras ideias, o Diego, mas
não aplicamos nenhuma ainda, porque assim não teve uma definição final
sobre o que faz sentido para o nosso negócio.

**Diego Souza** 35:59  
Então a gente tem um momento, a gente, a gente tem um momento bom. Agora
a gente chegou no momento bom de definir esse tipo de classificação,
porque, por exemplo, a gente tem uma eu Bahia, me corrija, eu tenho uma
pirâmide aqui que é.  
Faturamento, quantidade de máquinas no cliente e potencial. Esse é o
pilar que eu tenho. Então, quanto maior faturamento, maior número de
maior potencial é o cliente mais top que eu poderia ter.  
Tem casos, por exemplo, que eu tenho uma dificuldade, o Kelly, por
exemplo, de mensurar a Move, por exemplo. A Move, a base de dados dela
fica em outro sistema, né Bahia? Ela fica com o sistema dela. Eu não
tenho tanto acesso para saber quantos equipamentos de fato ela tem.

**Ederson Bahia** 36:45  
Machel também.

**Diego Souza** 36:50  
Como que eu vou mensurar uma conta dessa? Eu vou ter que se olhar só
aonde? No faturamento, entende? É. E falta ainda alguns dados para a
gente fazer esse tripé.

**Ederson Bahia** 37:03  
E isso acontece na Shell também. A Shell também eu não sei os
equipamentos que o pessoal tem lá, vibra e Iconic agora. E tem um
detalhe Rafael, não sei se a ferramenta talvez ela possa enxergar alguma
coisa que a gente não enxerga e sugerir algumas coisas, tá?

**Diego Souza** 37:06  
Shell vibra.

**Ederson Bahia** 37:20  
Por exemplo, às vezes eu estou falando com um cliente e naquele momento
ele quer se valorizar, ele quer mostrar que ele tem potencial e ele vai
falar que tem um milhão de máquina. Mas efetivamente ele não vai
monitorar tudo isso, ele monitora um pequeno universo. Então a gente
também tem dificuldade de enxergar que universo é esse.  
Esse real que ele está monitorando para ver o crescimento real e aí sim
encaixar ele na pirâmide que o Diego falou que faz sentido, tá? A ideia
de uma estrutura para a gente chegar ao cliente é aquilo ali mesmo, mas
alguns números a gente tem muita dificuldade em entender.  
Em descobrir, alguns a gente descobre, mas a gente ainda tem uma certa
dúvida, porque é comum o cliente no início fala que vai monitorar, manda
uma planilha para a gente gigante. Tem lá 300, 400 equipamentos, mas na
prática ele manda só de 50.

**Rafael Roriz** 38:14  
Qual que é o tamanho do? Na verdade, qual que é o tempo? Qual que é a
escala temporal da base de dados de vocês? Desde quando vocês monitoram
esses dados que eu vou ter acesso para?  
seguir os modelos, porque por uma visão temporal, nós podemos saber ter
uma maior acurácia em relação a esse tipo de classificação de cliente,
porque, por exemplo, se nós tivermos essas 3 regras da pirâmide.  
porém é tivemos uma variância grande entre o tipo de cliente é esse
cliente esse ano ele foi desse jeito no outro ano ele vai ele pode se
comportar daquela maneira entendeu então é  
Se nós enxergarmos a série temporal, nós podemos criar regras para que
os modelos que eu for criar terão uma maior manutenbilidade. Assim,
vocês vão ter menos necessidade.  
De atualizar os parâmetros do modelo em relação ao tempo. Vocês vão ter
um modelo que funcione por mais tempo. É isso que eu estou pensando. Por
ser um projeto fechado, deixar um modelo com vocês que.

**Diego Souza** 39:31  
That.

**Rafael Roriz** 39:33  
Vocês possam é manter.

**Diego Souza** 39:37  
é porque assim ó o que o que mais me quebrava Kelly você vai lembrar
disso é quando eu ouvi o seguinte a mas a Bayer é gigante ela é mundial
ela ela tem um potencial enorme mas aqui fazia 3 equipamento Bahia  
Aí a Bayer era colocada como um cliente bom, um cliente top, porque o
potencial dela é grande, lógico, multinacional, várias unidades. E aí a
gente tinha o feeling, né? O feeling.  
De falar aa

**Keli Ordoz** 40:10  
É o potencial de feeling, é isso aí é nenhum modelo vai conseguir ler,
então assim.

**Diego Souza** 40:16  
Não, porque ele é humano, pô, ele é humano.

**Keli Ordoz** 40:18  
É o potencial assim, o que a gente, o que se coloca no modelo é o que
tem de dado. Ele vai ler, ele vai identificar padrões e tal. Mas assim,
a gente realmente tem muita dificuldade disso e isso é uma coisa que eu
sempre bati muito com o Luis em várias reuniões, né?  
Que aí a gente mostrava lá o potencial e ele olhava o nome do cliente e
falava: Não, mas esse cliente potencial é muito maior. Esse é o
potencial dele diante do conhecido, do dado conhecido, do que a gente
conhece hoje, o que a gente tem na nossa base.  
Agora, o que a gente sonha que a gente acredita, mas ela é muito grande,
ela é motivacional e etc, etc.  
A gente fica no abismo, porque e assim, Eu Acredito que isso vai
continuar sendo assim, porque não tem como, né?

**Diego Souza** 41:07  
Porque eu vou ter fatos aqui.  
Edge.  
Okay.  
É exemplo, eu tenho aqui um grupo de usinas, são 8 usinas, só que eu
faço análise só em uma.  
você olhar o potencial da usina que eu tô trabalhando Ela tá no limite
ela faz tudo que ela pode fazer mas se olhar o grupo comercialmente
falando gente ela tem um potencial gigantesco mas para uma ela tá
fazendo  
Potencial daquela ali, ela tem 200 equipamentos, faz 800 amostra.
Potencial dela, CNPJ, está OK. Mas como um grupo ainda falta chão,
porque eu tenho que atingir 7 unidades. Então esse tipo de.  
De inteligência do negócio é até onde vai o sentimento humano, Diego?
Até onde vai o feeling humano que eu preciso tirar fora para gerar o
dado correto? Então em vendas é olhar para o Caio Caio, você é um cara
que gosta de relógio, pô, eu não conheço o Caio.  
Eu vou falar coisas para o Caio, para o Caio falar assim, pô, tem razão,
eu preciso de um relógio, sendo que ele eu não sabia, eu joguei, eu
joguei a informação em algum momento, ela foi capturada, então para mim
aqui é o Forecast.  
Passa por esse universo, que é eu ter o feeling, que é a gente ter o
feeling de um cliente potencial. Então, se a gente conseguir achar um
meio termo onde a inteligência hoje, a IA consiga cruzar dado e falar
assim, não, Diego, esse cliente aqui, ele é grande, você não está
trabalhando direito.  
Aí, beleza, a gente chega no X questão.

**Rafael Roriz** 42:54  
Eu acho o Caio também provavelmente entende assim que os modelos para
forecasting, essa parte de sentimental feeling, nós podemos trabalhar
com a análise de sentimentos.  
E podemos, é.  
de forma qualitativa, né? Saber  
Por que que esse cliente não está investindo, o cliente com um X
potencial não está investindo, e aí retornar para o potencial, para o
número do potencial? Porque, por exemplo, se a Bianca, igual vocês estão
falando aí do exemplo da Bianca.  
se ela trabalha com outras fornecedores de óleo, se aquela planta da
Barney trabalha DeX maneira, a Barney tem um potencial, mas ela vai
comprar, ela vai precisar, ela vai ter a necessidade, nós vamos
conseguir  
criar a necessidade nela então isso vai os dados vão bater e vão
retornar no potencial entendeu aí é isso que eu penso que penso também
numa parte mais de LLM mesmo que é uma parte mais  
É verbosa, mas de análise mesmo de sentimento. Ah, o que que é? Quando
que ele pode fazer? Isso aqui é realmente um sentimento? Isso aqui é só
o fim humano mesmo? É como que ela pode é investir? Ela vai investir?
Como que foi?  
11 parceria passada com outra fornecedora igual como ela trata as outras
fornecedoras, isso pode retornar ao padrão, ao número de potencial e
diminuir ou aumentar, entendeu? Pra poder saber se realmente.  
É uma, é um problema do trabalho, da do financeiro, ou se o potencial é
menor mesmo, porque pode ser que ele seja menor, entendeu? É a análise
de sentimento pode contribuir com isso, entendeu?

**Caio Alcantara** 45:02  
Eu tenho uma dúvida também, hoje a gente tem tipo no cadastro do cliente
em si, por exemplo, igual você mencionou desse cliente que a gente
atende uma usina, dentro dessa usina a gente está no potencial máximo
que a gente poderia atender, mas ele tem mais outras sede que a gente
poderia estar atendendo.  
Hoje a gente já possui algo para identificar, por exemplo, que
existiriam essas outras 7 tipo dentro do cadastro do cliente.

**Keli Ordoz** 45:27  
Não, hoje, hoje, na verdade.  
É, a gente tem até uma estrutura dentro do CRM que são.  
Conta matriz e filiais, mas isso não está atualizado, mas geralmente a
gente só usa também para as contas existentes. Então aí eu cadastrei 5
unidades e aí eles criam lá a hierarquia e já fazem esse vídeo.  
Então a gente fala de contas que existem de fato, que são clientes. Não
temos nenhum campo hoje para, tipo, colocar assim, potencial, unidades
não rastreadas, sei lá, coisa do tipo.

**Caio Alcantara** 46:05  
Potencial.

**Diego Souza** 46:11  
É porque a gente boa, boa, boa essa provocação. A gente está conversando
e chegando num consenso. Por exemplo, aqui a gente está falando forecast
de clientes existentes. A gente não está entrando nessa Seara aqui, por
exemplo.

**Keli Ordoz** 46:12  
sete oito um campo assim vem

**Diego Souza** 46:27  
De reativar ações que acontece dentro do mês e nem clientes novos. A
gente está falando de uma receita recorrente para clientes ativo. O
Diego, então você pode ter uma receita durante o mês de dessas 2
vertentes? Sim.  
de reativações e clientes novos. A gente não vai entrar com elas aqui no
grosso, mas a gente poderia usar elas no futuro, tá? Se a gente acertar
a recorrência baseada em composição de projeção de consumo de amostras
dos ativos, já é uma vitória. A gente consegue acertar as outras duas.  
a gente tem vários números de vendas novas e reativação também que a
gente tem dados agora também mas o ponto aí cara que a Kelly falou é eu
ter um cliente na minha ativo ele tem um potencial ativo ali ele pode
chegar no 100 por cento  
Olha hoje 100% o fulano de tal faz amostras o Bahia a calculadora do
Bahia indica que ele atingiu 100%. Tá e agora o que que eu faço depois
disso? Ele vai ter uma recorrência, tá? Então o objetivo do teu time
Diego é manter esse 100% sim.  
Porque ele vai consumir o máximo que ele pode me entregar. A partir daí,
aí eu vou trabalhar com prospecção, vou trabalhar para puxar as outras
contas. E aí, beleza. Mas o ponto é, até hoje a gente não consegue falar
assim, esse cara aqui, ele faz 100% do que ele precisava fazer? Às
vezes, hoje a gente não tem isso dado.

**Keli Ordoz** 47:59  
E até porque assim, mesmo se a gente tivesse um campo, falasse assim,
esse cliente aqui, cliente A, que é um cliente que nós temos hoje, ele
tem mais sete filiais que nós não temos cadastro, a gente não vende
nessas filiais e tal.

**Diego Souza** 48:00  
Okay.

**Keli Ordoz** 48:14  
tivéssemos um campo assim e fôssemos usar esse campo para ajudar em
algum cálculo. Seria um campo muito irreal, porque, por exemplo, ele
pode ter sete plantas, mas todas as plantas são do mesmo tamanho.  
daquela não entendeu eu posso ter assim uma empresa ela pode ter uma que
é muito uma planta muito pequena outra muito grande a outra média né
então é eu acho assim que o sentido como o dia que falou é a gente  
Entender o que a gente tem para explorar no cliente que a gente tem
hoje, a gente já tem ele hoje dentro da empresa e a gente não consegue
ver de uma maneira clara se ele está executando o 100% do potencial de
amostras que eu.  
De acordo com os equipamentos que ele tem, o segmento que ele é, o
benchmark de outros clientes do mesmo setor, que tem as mesmas máquinas,
que tem um padrão já muito bom de aderência do plano de amostras.  
Por que o outro coleguinha faz se ele não faz? O outro atinge 80% do
potencial, ele faz só 25 do que ele deveria fazer. Então é essa visão
clara que ajuda na venda, que.  
Basicamente, é o potencial que, de uma certa forma, se transforma no
forecast que a gente tem com esse cliente.

**Caio Alcantara** 49:46  
Aí entra também muito naquela na questão ali tipo da previsão real e
da.  
Dá prevista no caso da gente que eu tinha até mostrado aqui pros meninos
mais cedo.

**Ederson Bahia** 49:57  
Isso mesmo, é aquilo lá mesmo, 200 e 400.

**Caio Alcantara** 49:59  
Santa quina real em potencial.

**Keli Ordoz** 50:07  
Tudo aqui falando exatamente isso, porque o real é baseado no histórico
que ele já tem conosco, né? E o potencial é baseado num outro fator, né?
É o que a gente gostaria que ele fizesse, o que ele  
poderia fazer e é esse potencial que o pessoal vai atacar de uma maneira
mais técnica para conseguir. E o real é meio que a obrigação, né? Tem
que atingir, porque se ele já fazia, por que ele não está fazendo?

**Ederson Bahia** 50:36  
A.  
Só quero aproveitar, Rafael, o slide aqui e veja que eu tenho que
comparar os equipamentos cadastrados com alguma coisa. Isso vai variar.
Vai ser preciso também entender e criar talvez uma regra para esses
equipamentos cadastrados.  
Porque eu tenho clientes que já são clientes nossos há mais de 10 anos,
então tem equipamento cadastrado na plataforma que não está mais ativo
para o cliente, tá? E o cliente às vezes não informa isso para a gente,
então no.  
No sistema nosso, eu tenho até uma coluna lá para mim poder manter
aquele equipamento ativo ou não, mas nem sempre o cliente me avisa isso.
Então, se eu olhar de forma fria para esse número, eu não poderia,
porque eu vou ter ali equipamentos que  
Que já não existem mais, então eu tenho que pensar também numa forma de
desconsiderar. E aí a gente pode conversar depois como é que a gente
trabalharia aí, se seria por período, se seria por segmento, se vai
trabalhar por, sei lá, 5 anos e deu, mas depois a gente tem que pensar
alguma coisa nesse sentido também.  
Tá, porque existe equipamentos na plataforma cadastrados que não
existem.

**Rafael Roriz** 51:53  
provavelmente será por todo isso será que por período e segmento né E
por usando utilizando o modelo estatístico né É porque o período ele
pode o período ele constitui uma  
A série temporada é igual havia falado antes e o segmento, ele constitui
a parte ordinal, que é a parte qualitativa, então é o segmento.  
Por exemplo, nós temos segmento de cana de açúcar, qual que é a
recorrência de abandono do equipamento ou de renovação de frota do
equipamento?  
Então, dessa maneira, nós conseguimos constituir uma regra em outro
modelo estatístico. Então teremos um modelo estatístico provavelmente
também para isso, para poder saber.

**Ederson Bahia** 52:55  
É, a gente pode pesquisar talvez por é, pode pesquisar talvez por tempo
de vida útil do equipamento, ele pode ajudar.

**Diego Souza** 53:01  
É, qual que é a média de uma colhedora de cana? Eu falo para vocês 7
anos.  
7 anos ela já se troca. Então se eu calculo o equipamento, que dia que
ele foi cadastrado, eu conto 7, ele já não existe mais. Eu já não
considero ele mais na base estatística. A gente consegue esses dados
Rafael, a gente tem vários contatos aqui que a gente consegue
levantar.  
Mas o ponto, Caio, você tocou num ponto aí falando sobre real e
potencial, porque olha que interessante aonde a LS mira o crescimento. É
quando eu olho para minha base real.  
Olho l e falo, ô, pera aí.  
Dentro da minha base real, eu tenho um potencial.  
Porque eu sei que a minha base real hoje ela não é feita da maneira
correta, ela não é feita 100%. Eu tenho chances de crescer dentro da
minha base. Então se eu for falar dos meus clientes que fazem 200
amostras mês, ele.  
Faz 200 amostras, mas eu sei que o potencial dele é fazer 600, 100, 200,
20, 40% a mais. É aonde todos os esforços que nós hoje do time
comercial, marketing e CS faz.  
É que todos os clientes atinjam o potencial que eles têm que atingir
para a gente crescer, para a gente continuar crescendo e batendo as
metas, os objetivos que a gente tem. Então é.  
É muito, é fundamental entendermos o potencial para ver aonde, até onde
a gente pode chegar.  
Está aonde eu vou gastar meu esforço? Se é em pré-venda, é trazendo o
cliente, é reativando o cliente, é trabalhar no que eu já tenho. Então
essa é o X da questão.

**Caio Alcantara** 54:49  
Mais direcionado, né?

**Diego Souza** 54:51  
Isso.

**Rafael Roriz** 54:52  
Eles são é 2 números, 2 erros diferentes, mas é um está dentro do outro,
o real está dentro do potencial no sentido de crescimento.  
então a correlação vai ser muito importante para saber o que que é o
verdadeiro real e o que que vai ser o potencial né fazer uma predição
acima da melhor com melhor acurácia do que a atual né  
Carvalho.

**Diego Souza** 55:24  
Thanks.

**Caio Alcantara** 55:31  
Bom pessoal, é.  
que a gente já fez as validações né o que tinha ficado pendente e para
finalizar é só realmente explicar para vocês como a gente vai trabalhar
né essa reunião foi de fato para a gente pontuar o que a gente já tem
mensurado para identificar  
Justamente para a gente fazer essas discussões, pontuar se está tudo
certo e fazer as validações. E agora também eu e o Rafael a gente vai
conseguir com esses dados, a gente vai validar tudo e a gente vai
validar também se as métricas que a gente tem, se elas de fato são as
mais adequadas ou se a gente.  
Pode trazer algo ainda melhor, a gente pode trazer alguma curacidade
ainda melhor, trabalhando e explorando os dados que a gente já tem. E se
alguma coisa a mais, alguma alteração, alguma adição, alguma remoção
fizer sentido, a gente vai sugerir alguma abordagem diferente para
melhorar a curacidade, se for necessário.  
Mas sempre mantendo contato com vocês para a gente fazer as validações e
mostrar os resultados que a gente tem alcançado também.  
E os próximos passos, basicamente, agora vão ser a gente fazer essas
validações. O Rafael, ele já está explorando os dados ali, já está, já
tem acesso ao ambiente, então a gente vai validar, a gente vai
identificar quais vão ser as melhores abordagens.  
E estando tudo certinho, a gente vai partir para a construção, depois é
a entrega desses resultados.

**Diego Souza** 56:59  
Muito bom, muito bom, pessoal. Para dados aqui, a Kelly sabe muito mais
do que nós. O Bahia também lida com os dados. Eu sou só a parte
comercial, gente. Eu só estou aqui só toca a parte comercial.  
É.  
o nível de informação que a gente chegou eu cheguei aqui em 2018 três
meses antes da Keli né Keli três meses antes da Keli que ele entrou acho
que dezembro você entrou né dezembro acho que dezembro novembro

**Keli Ordoz** 57:28  
A gosto de Deus foi, é gosto, foi.

**Diego Souza** 57:30  
Água.  
A gente entrou um pouco antes e quando a gente chegou, Kelly, era tudo
mato, lembra? Era tudo mato. A gente não tinha esse nível de dados que
hoje a gente tem. E a gente passou por vários períodos aí de BI, de
construção, de CRM, hoje.  
A gente tem um nível de informação que quando eu mostro para algumas
pessoas próximas, fora do eixo LS, você fala, pô, bacanas, nem na
empresa nossa não tem, são empresas grandes. Vocês chegaram nesse nível
bacana, foi muito trabalho, foi muito trabalho. Primeiro trabalho da
Kelly, muito bem feito.  
trabalho também de técnico da do Bahia então usem eles aproveitam o
conhecimento que eles têm é aquele nos ajuda bastante com muitas coisas
né paralelas né a dados né que é para lá muito mais hoje CRM né que ela
pois dá para rodar

**Keli Ordoz** 58:21  
Não da lela.

**Diego Souza** 58:27  
Então, a ajuda é muito boa para nós. A gente agradece a ajuda de vocês
dois aí e espera bons resultados.

**Keli Ordoz** 58:33  
A gente ainda tem bastante dificuldade com padrão. Padrão de dados é uma
luta constante, constante, constante. Eu falo a mesma coisa há muitos
anos.  
Sobre que antes da gente querer automatizar, né? Hoje tudo assim, vamos
fazer isso automático, vamos fazer, é lindo, mas as informações tem que
estar corretas, tem que ter um certo padrão, né?  
Então, assim, tem muitas dificuldades ainda nisso. O CRM que a gente
mudou, né, recentemente, a gente tinha dynex, foi para o Zorro. Hoje o
Zorro, e até quero deixar isso aberto para vocês entenderem também, o
Zorro é o CRM.  
Então, ele é um software muito simples de ser configurado. Então, por
exemplo, se vocês pensaram assim, nossa, seria muito bom se a gente
tivesse um campo lá que tivesse X informação.  
num determinado padrão. É muito fácil de fazer um campo, né? Ou
inclusive criar fluxos de informações obrigatórias. Então, assim, é esse
negócio de informações obrigatórias. Eu tento cercar muito no CRM.  
Justamente para a gente ter um padrão de dados, porque depois, no final
das contas, é esse padrão que vai ajudar a gente a entender várias
outras coisas. A gente já conseguiu padronizar, por exemplo, a questão
de códigos, que parece que é uma coisa muito, é muito simples, o código
do cliente.  
Mas não existia essa identificação lá em 2018. O cliente tinha um código
no faturamento, não existia o código no S360, não existia esse código
CRM. Então, assim, a gente fez todo esse trabalho para popular o início,
o código.  
É código de produto de venda, hoje é padronizado, mas dentro do Santos
360, se a gente quiser cruzar o produto que ele comprou, é o produto que
ele está processando.  
Não sabemos porque não existe padrão no Santos 360. É, existe uma das
coisinhas no Santos 360, tipo amostra sem equipamento vinculado. Aí,
como que você vai traçar uma linha de potencial?  
Se é uma amostra avulsa. É uma amostra avulsa, né? A gente se deparou
muito com isso também. Então, assim, já melhorou, mas ainda existe muita
melhora a ser feita que vocês vão descobrir na hora que tiver mais
afundando nos dados de

**Caio Alcantara** 1:00:57  
Thanks, Aan

**Keli Ordoz** 1:01:12  
Padrão e assim podem contar comigo em coisas que vocês acharem. Ah,
seria legal se a gente conseguisse padronizar isso. É em algum dos
sistemas, principalmente o que a gente está agora fazendo, trabalhando a
integração do Proteus com o Muzol e com Sa  
Então, a gente está tentando padronizar, pelo menos o nível cadastral
vai ser padronizado e depois a gente tem que ligar para outros, outros
dados. Eu não queria falar isso porque eu acho que isso é a base, a base
de  
tudo. A gente ter dados assim, com um padrão adequado, né? A gente não
consegue muita coisa.

**Caio Alcantara** 1:01:53  
Perfect.

**Diego Souza** 1:01:53  
É porque no final das contas, o comercial aqui é muito responsável por
isso, porque ele é a ponte de pegar a informação na rua, trazer para
dentro de casa e trazer da maneira correta, para que quando vocês usarem
esses dados para fazer a inteligência, a predição.  
Pô, você fala assim, pô, será que esse time do Diego tá trazendo esses
dados certo? Que se fizer errado, dá \*\*\*\*\* lá na frente, não sai um
dado real. Então é, se vocês, bom, Diego, a gente vai precisar do seu
time muito forte na questão de  
equipamentos isso aqui tem que ser bem feito aí aqui ele vai botar uma
trava lá e o cara não consegue vender esse mês se não tiver o campo lá
do equipamento cadastrado então aí seria uma trava por exemplo que a
gente pode criar né Kelly

**Keli Ordoz** 1:02:42  
A.  
É, a gente já fez várias travas, já fez várias travas e a gente já fez
várias ações também, que também já deixa velho para vocês, que às vezes
vocês vão começar a olhar. Nossa, está faltando X informação, a gente
precisa fazer uma.  
força tarefa de preenchimento dessa informação. A gente fez muito isso
com a equipe comercial, mas os setores segmento, que é uma coisa
extremamente importante para a gente entender comportamentos, não
existia. A gente pegou lá os clientes mais importantes no começo.  
e deu o prazo para os vendedores atualizar todo o setor de segmento das
empresas, né? E assim foi assim, durante esses anos, muitas tarefas
desse tipo para tentar deixar um número de informação para a gente. Mas
é isso.  
E eu tenho uma pergunta que eu queria saber, por exemplo, o planejamento
de vocês é, vocês vão entregar esses resultados? Em qual formato a gente
vai ter um?  
É tipo.  
up com esses dados que eles vão estar lá pra gente, por exemplo, eu, o
Max, vou sumir o dado, jogar esse dado, esse resultado que vocês vão
conseguir encontrar pronto para a gente alimentar, por exemplo, algum  
Power BI existente que a gente tem, ou vocês já vão entregar isso num
formato novo de tipo, já existe um formato de relatório que vai ser
alimentado por ele, então para eu entender.

**Caio Alcantara** 1:04:18  
A.  
A entrega do Rafael, de fato, é uma base de código, então não é algo
assim que a gente vai fazer mais de forma interna depois que ele
finalizar, para de fato entregar alguma coisa. O objetivo final é que a
gente tenha um agente com o conhecimento desses dados.  
Só que o agente ainda vai demorar mais um tempo para de fato ficar
pronto. Então, porque a gente está considerando aqui só duas métricas,
que é forecast de vendas e consumo de amostras. Mas a gente tem diversas
outras métricas e questões que esse a gente vai trabalhar, então o
agente vai demorar muito mais.  
Só que é no caso, como é com esse modelo que o Rafael vai entregar, a
gente pode fazer tipo um HTML, que seria tipo um relatório assim. Vou
até mostrar um exemplo para vocês de alguns que a gente já trabalhou lá
para o laboratório.  
Pra vocês terem uma noção mais ou menos de como que ficaria também.

**Rafael Roriz** 1:05:24  
Eu penso que seriam HTML no estilo painel, dashboard no estilo BI, com a
opção de exportação para diferentes formatos e também vou conversar com
o Caio e também  
Tem o outro engenheiro, o engenheiro de dados, sobre fazer como se fosse
outra camada, porque vocês têm uma camada Gold que é para um agente
específico, talvez fazer outra camada Gold ou outro medalhão dentro só
desse dessas métricas, entendeu? Com.  
Diferentes bancos de dados e aí vocês consulta por SQL, pelo menos é
isso que eu penso.

**Keli Ordoz** 1:06:00  
É, então é.  
Se a gente conseguisse consultar por SQL seria muito bom porque assim é
eu entendo que a gente vai ter o resultado pronto né que pode já tá numa
visualização que é legal vocês vão fazer mas a gente também tem essa
liberdade de tipo ah eu quero pegar esse dado e incorporar ele  
Aqui num outro relatório que a gente já tem aqui para juntar com outras
informações que talvez a gente tem. Então esse outro formato também para
nós seria muito bom.  
Se fosse possível.

**Caio Alcantara** 1:06:37  
Espera aí, desculpa, eu tava abrindo aqui, não ouve o que você falou,
você pode repetir de novo?

**Keli Ordoz** 1:06:42  
Da gente ter acesso como SQL ou como qualquer outra fonte de dados
mesmo.

**Caio Alcantara** 1:06:50  
É, ele ficaria tipo como se fosse um Power BI, só que ele ficaria
consumindo os dados direto do banco de dados mesmo. Então, por exemplo,
ele estaria ali consumindo todos os dados do S360 do Zorro.  
E do Proteus, convertendo, tratando todos esses dados e trazendo para cá
um exemplo.

**Keli Ordoz** 1:07:09  
Mhm.

**Caio Alcantara** 1:07:11  
Vou mostrar aqui para vocês um exemplo do que a gente já tem do
laboratório para vocês terem uma ideia mais ou menos de uma ideia de
como ficaria, mas isso aqui é totalmente adaptável. A gente pode fazer
no formato assim que fizer mais sentido para vocês.  
Mas aqui, basicamente, esse daqui é um HTML que o pessoal já utiliza lá
no laboratório. Aí aqui, por exemplo, a gente define, tipo, é
basicamente para a gente identificar, tem um overview de como que está o
TaT.

**Keli Ordoz** 1:07:29  
Mhm.

**Caio Alcantara** 1:07:40  
Aí, basicamente aqui o pessoal pode definir, tipo qual que é o
laboratório, qual que é o mês, a data, se bateu o tite ou não, qual que
é o prazo referente à amostra, se tem reanálises ou não, pode selecionar
algum pacote específico.  
Aí aqui, dependendo de como a gente mexe nos filtros, ele vai alterando,
sabe? Então é como se fosse de fato um Power BI, só que algo muito mais
personalizável. Como a gente está fazendo com IA, a gente tem total
flexibilidade para entregar o formato que mais fizer sentido para vocês.

**Keli Ordoz** 1:08:13  
It is.

**Caio Alcantara** 1:08:17  
Inclusive, tem até um que o Milani tinha pedido esses dias para trás,
referente a bem similar a esse daqui também, só que com outro objetivo.
Então, assim, a gente pode pensar em outras abordagens também, mas
inicialmente eu penso que talvez essa seria a forma mais simples e
didática também da gente abordar.  
os dados que a gente vai trazer, mas a longo prazo o objetivo de fato é
que o agente que a gente vai fazer para o CRM tenha esse conhecimento
desses dados.

**Diego Souza** 1:08:44  
É, ficou muito. Acho que eu acho que esse, esse, esse tá rodando já não,
se eu não me engano, ele já tá rodando no lab. Esse aí, né? Eu vi uma
telinha parecida com esse com a Flávia. A Flávia já tá trabalhando. O
que que tá acontecendo? O Caio essa ideia do Milani.

**Caio Alcantara** 1:08:54  
Thank.

**Diego Souza** 1:09:01  
Que casa com a projeção de consumo de amostras é muito comercial, porque
se essa informação lembra mim, por exemplo, Diego, o cliente fulano foi
o que mais consumiu amostras nesse período. Eu vou lá, vejo a última
compra dele. Foi há 3 meses atrás.  
Pô, o volume que ele consumir esse mês está absurdo. Ele vai precisar de
frascos, então já vou direto nele e falo, olha, você não quer fazer uma
nova compra, tá? Então.  
É um dado muito bom para nós.

**Caio Alcantara** 1:09:36  
O.  
Bom pessoal, então tem mais algum ponto, mais alguma coisa que você
gostaria de trazer, algo ponto A?

**Diego Souza** 1:09:46  
Da minha parte está tranquilo, gente, acho que a gente pode falar.

**Ederson Bahia** 1:09:48  
Da minha parte também, só mais uma vez falar com Rafael e Caio que estão
à disposição. Se precisar é só chamar.

**Caio Alcantara** 1:09:55  
Not.

**Diego Souza** 1:09:56  
Mais alguma dúvida, Keli?  
Tá no mudo.

**Caio Alcantara** 1:10:00  
Ótimo. Então, pessoal, muito obrigado pelo tempo de vocês. É um ótimo
trabalho para todo mundo.

**Keli Ordoz** 1:10:01  
Thank you.

**Diego Souza** 1:10:04  
Imagina.

**Rafael Roriz** 1:10:06  
Valeu, muito obrigado!

**Diego Souza** 1:10:06  
Obrigado, boa sorte aí no projeto.

**Ederson Bahia** 1:10:09  
AAP. That mine, tchau.

**Rafael Roriz** 1:10:10  
Tchau, tchau. Estou à disposição aqui também, viu? Qualquer pergunta.

**Diego Souza** 1:10:10  
Até mais gente.

**Keli Ordoz** 1:10:10  
Tchau, tchau.

**Diego Souza** 1:10:14  
Beleza, Rafael, valeu!

**Rafael Roriz** 1:10:16  
So we got to.

**Caio Alcantara** 1:10:16  
Control.

**Caio Alcantara** stopped transcription
