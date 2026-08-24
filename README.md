# Evidências da comparação técnica Lighthouse

[![Validar evidências](https://github.com/xndvaz/mba-eca-usp-transformacao-digital/actions/workflows/validar-evidencias.yml/badge.svg)](https://github.com/xndvaz/mba-eca-usp-transformacao-digital/actions/workflows/validar-evidencias.yml)
[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/xndvaz/mba-eca-usp-transformacao-digital/releases/tag/v1.0.0)

Este repositório reúne os materiais de pesquisa associados ao trabalho **Arquitetura de conteúdo orientada por dados em veículo independente: IA generativa e comparação técnica**, de Alexandre Martins Vaz dos Santos, no MBA em Gestão e Transformação Digital da Escola de Comunicações e Artes da Universidade de São Paulo.

O conjunto documenta uma comparação técnica transversal entre o Nintendista News e seis veículos brasileiros do mesmo nicho. Foram auditadas a página inicial e uma notícia interna de cada veículo, em perfis mobile e desktop, com cinco repetições por combinação. O desenho totalizou `7 × 2 × 2 × 5 = 140` auditorias válidas no Google Lighthouse 13.4.1.

## Conteúdo

- `protocolo/`: manifesto das 14 URLs, ambiente, protocolo e registro das 140 execuções;
- `dados/`: dados consolidados, medianas, intervalos interquartis e resultados de Agentic Browsing;
- `integridade/`: hashes SHA-256 e conferência dos relatórios;
- `scripts/`: consolidação, validação, tabelas e figuras;
- `assets/fonts/`: DejaVu Sans 2.37 usado para geração visual determinística;
- `CITATION.cff`: metadados para citação;
- `licencas/`: termos aplicáveis ao código, aos textos e aos dados derivados.

Os 140 relatórios JSON originais estão no arquivo `lighthouse-json-140-v1.0.0.tar.gz` da [release v1.0.0](https://github.com/xndvaz/mba-eca-usp-transformacao-digital/releases/tag/v1.0.0). O hash SHA-256 do arquivo consta em `integridade/sha256-arquivo-release.txt`, e a conferência do pacote está documentada em `integridade/registro-arquivo-release-v1.0.0.md`. Os relatórios HTML e os demais registros internos permanecem sob guarda do autor.

## Delineamento e seleção

A seleção foi intencional. Uma pesquisa exploratória inicial mapeou veículos brasileiros em língua portuguesa dedicados ao universo Nintendo. Entre os identificados, foram escolhidos seis que, segundo a experiência prévia do autor, apresentavam presença recorrente nas comunidades nintendistas e mantinham páginas públicas acessíveis no período da coleta. Essa presença não foi mensurada por audiência, receita ou participação de mercado. O conjunto não constitui ranking nem levantamento exaustivo, e o julgamento do pesquisador configura possível viés de seleção.

O estudo avaliou apenas indicadores sintéticos do Lighthouse. Os resultados não medem qualidade jornalística, audiência, reputação, produtividade, experiência real de usuários ou causalidade. Publicidade, integrações de terceiros, conteúdo, CDN, servidores, máquina e rede podem afetar cada execução.

## Reprodução e verificação

Requisitos: Python 3.11 ou superior. A consolidação e a validação usam apenas a biblioteca padrão; a regeneração das figuras requer Pillow.

```bash
tar -xzf lighthouse-json-140-v1.0.0.tar.gz
python3 scripts/consolidar-resultados.py \
  --raw-dir relatorios-json \
  --out /tmp/resultados-regerados
python3 scripts/validar-pacote.py \
  --raw-dir relatorios-json \
  --rebuild
python3 -m pip install -r requirements.txt
python3 scripts/gerar-tabelas-figuras.py
python3 scripts/gerar-figura-escores.py
python3 scripts/gerar-resumo-redacao.py
```

A automação do repositório baixa a release, confere a quantidade de arquivos, os hashes e a regeneração dos dados consolidados. As tabelas e figuras regeneradas ficam em `figuras-geradas/`. A comparação visual exige dimensões idênticas e usa limites estritos nos gráficos. Nas tabelas, pequenas diferenças de rasterização entre versões do FreeType são admitidas somente quando uma máscara independente, sem as linhas de grade, confirma a preservação da estrutura textual.

## Integridade e privacidade

Os JSON foram preservados sem alteração. Antes da publicação, o conjunto foi verificado contra caminhos locais, endereços pessoais, cabeçalhos de autenticação, chaves privadas e formatos conhecidos de credenciais. Os relatórios registram recursos e metadados fornecidos publicamente pelos sites auditados, inclusive integrações e publicidade de terceiros.

Nenhum código-fonte do Nintendista News, conversa, documento institucional, monografia, relatório HTML, formulário, artefato exploratório de IA ou credencial integra este repositório.

Relatos de segurança devem seguir a [política de segurança](SECURITY.md), que orienta o uso do canal privado do GitHub. A automação opera com permissão somente de leitura, dependências monitoradas e ações fixadas por identificadores imutáveis.

## Direitos

Os nomes, marcas, URLs, textos, imagens e demais recursos dos sites auditados permanecem sob os direitos de seus respectivos titulares. Sua presença nos relatórios deriva da observação automatizada de páginas públicas para fins acadêmicos e não transfere direitos ao autor deste conjunto. Consulte `DIREITOS-E-LIMITES.md` e as licenças específicas.

Os arquivos DejaVu Sans 2.37 usados pelos geradores visuais são distribuídos nos termos de `assets/fonts/LICENSE-DejaVu.txt`.
