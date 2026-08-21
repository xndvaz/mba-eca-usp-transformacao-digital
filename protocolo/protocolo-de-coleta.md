# Protocolo de coleta - Google Lighthouse

## Delineamento

Comparação técnica transversal de páginas públicas de sete veículos brasileiros com conteúdo sobre Nintendo. A coleta compara o Nintendista News a seis veículos do mesmo nicho, sem desenho de antes e depois e sem inferência sobre audiência, qualidade jornalística, produtividade ou causalidade.

## Seleção das páginas

A seleção das 14 URLs foi fixada em 20 de agosto de 2026. Antes da nova coleta oficial, os mesmos endereços foram verificados quanto à disponibilidade. A manutenção das URLs evita alterar simultaneamente o conteúdo e o instrumento de coleta. Para cada veículo, permaneceu definida a página inicial e a notícia convencional selecionada pelo protocolo original. Reviews, análises, ofertas, páginas especiais, listas semanais e conteúdos interativos foram excluídos.

Uma ocorrência será tratada como limitação documentada:

- A Casa do Cogumelo não exibia notícia convencional elegível na página inicial. Para não substituir uma notícia por uma análise, foi selecionada a publicação convencional mais recente localizada no sitemap público. A comparação dessa interna deve ser interpretada com cautela porque a data de publicação difere substancialmente das demais.

Uma auditoria-piloto da categoria Agentic Browsing foi executada antes da coleta, preservada em `99_Auditoria_Piloto_Descartada` e excluída da série analisada. A coleta anterior, que não incluiu essa categoria, foi arquivada integralmente e não será misturada ao novo conjunto.

O arquivo `protocolo/manifesto-de-urls.csv` preserva título, URL, código HTTP observado e justificativa de seleção.

## Ambiente e execução

- Google Lighthouse: 13.4.1;
- Google Chrome: 151.0.7922.172;
- mesma máquina, conexão e janela contínua de coleta;
- perfis: mobile padrão do Lighthouse e desktop com `--preset=desktop`;
- categorias: Performance, Accessibility, Best Practices, SEO e Agentic Browsing;
- cinco repetições por combinação de página e perfil;
- ordem dos veículos rotacionada entre as repetições para reduzir a associação entre horário e veículo;
- cada auditoria inicia uma instância limpa e sem extensões do Chrome;
- relatórios JSON e HTML integrais preservados.

O total planejado é `7 × 2 × 2 × 5 = 140` tentativas. Uma tentativa com erro continua no registro, mas não produz valor imputado e não entra nas medianas.

## Variáveis

Serão extraídos os escores de Performance, Accessibility, Best Practices e SEO, além de First Contentful Paint (FCP), Largest Contentful Paint (LCP), Speed Index, Total Blocking Time (TBT) e Cumulative Layout Shift (CLS). Os quatro escores consolidados serão apresentados em escala de 0 a 100; as métricas temporais, em segundos ou milissegundos conforme indicado; CLS é adimensional.

Agentic Browsing será tratado separadamente por seu caráter experimental e por usar exibição fracionária, e não escore ponderado de 0 a 100. Para cada auditoria serão preservados resultado, modo de exibição e classificação como aplicável ou não aplicável. Resultados não aplicáveis não serão convertidos em reprovação nem em zero.

Para cada combinação válida de página e perfil, serão calculadas mediana, primeiro quartil e terceiro quartil. Os quartis usarão interpolação linear sobre as cinco observações ordenadas. Não serão aplicados testes de hipótese nem estimativas populacionais.

## Integridade e limites

Cada arquivo receberá SHA-256. O registro consolidado conterá URL solicitada, URL final, perfil, repetição, início, término, versão do Lighthouse, código de erro e nome do relatório bruto. A execução não controla alterações do conteúdo, publicidade, scripts de terceiros, CDN, carga dos servidores ou variações da rede; por isso, os resultados representam apenas a janela observada.

O Lighthouse é uma ferramenta de auditoria sintética. Seus resultados não equivalem a dados de usuários reais e não permitem concluir, isoladamente, que um veículo possui melhor experiência percebida, maior audiência ou maior competitividade.
