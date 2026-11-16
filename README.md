# VisionBox

> Seu cinema inteligente: do app direto para a parede da sua casa.

O VisionBox é um app de cinema, no estilo Apple TV, feito para **rodar dentro de uma case em formato de projetor**. O computador fica ligado ao projetor, que funciona como monitor, e o app mostra o catálogo, a lista e o player direto na parede.

Projeto da **ExpoTech 2026.2 · Missão 2050 · Categoria FOUNDATION** (Smart Home & Tecnologias do Futuro).

**Tecnologias:** Python (Flask), MySQL, HTML, CSS e JavaScript.

---

## O que o sistema faz

- Login e cadastro, cada pessoa com a sua conta.
- Catálogo de filmes, séries, documentários e shows ao vivo.
- Busca e filtros por categoria.
- **Minha lista** e **Continuar assistindo** (o player lembra onde você parou).
- Modo claro e modo escuro.
- Navegação só com **setas e Enter** (teclado ou controle remoto) e tecla **F** para tela cheia.
- Funciona **sem internet**: capas, banners e trailers já estão no projeto.

---

## Como funciona

```
Navegador (tela do projetor)  →  Flask (app.py)  →  MySQL (banco "visionbox")
```

1. Você abre o app no navegador do computador ligado ao projetor.
2. O Flask busca no MySQL o catálogo, a sua lista e o seu progresso.
3. O vídeo (MP4 da pasta `static/videos`) toca na tela.
4. A cada 5 segundos o app salva onde você parou.

---

## Como iniciar

Funciona em qualquer computador. Você precisa de:

- **Python 3.10 ou mais novo** ([python.org](https://www.python.org/downloads/)). No instalador, marque **"Add python.exe to PATH"**.
- **MySQL** instalado e ligado.
- Internet na primeira vez, para instalar as dependências.

Abra o terminal **na pasta do projeto** (onde está o `app.py`).

### Primeira vez (só uma vez em cada computador)

**1. Criar o ambiente do Python e instalar as dependências**

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No Linux ou Mac, troque `.venv\Scripts\python.exe` por `.venv/bin/python`.

**2. Colocar a senha do MySQL no `.env`**

Se o `.env` não existir, copie o `.env.example` e renomeie para `.env`. Depois edite:

```
DB_USER=root
DB_PASSWORD=sua-senha-aqui
```

**3. Criar o banco, as tabelas e o catálogo**

```bat
.venv\Scripts\python.exe scripts\init_db.py
```

**Ao atualizar uma versão anterior do VisionBox:** execute novamente esse mesmo comando. Ele adiciona a coluna de visibilidade que o painel precisa sem apagar usuários, vídeos ou títulos existentes. Não use `--reset`, pois essa opção apaga as tabelas e contas.

### Todo dia (para usar)

Com o MySQL ligado:

```bat
.venv\Scripts\python.exe app.py
```

Abra **http://127.0.0.1:5000**, crie uma conta e aperte **F** para a tela cheia.

### Painel administrativo

As credenciais do administrador ficam em um arquivo separado, para você não precisar editar o código nem criar uma conta comum antes.

1. Na pasta principal do projeto, copie `admin.env.example` e renomeie a cópia para `admin.env`.
2. Abra `admin.env` e preencha `ADMIN_NAME`, `ADMIN_EMAIL` e `ADMIN_PASSWORD` com os dados que deseja usar no painel. Use uma senha forte com pelo menos 8 caracteres.
3. Com o MySQL ligado e o banco já criado, execute uma vez:

```bat
.venv\Scripts\python.exe scripts\configurar_admin.py
```

O script cria a conta administrativa. Se o e-mail já existir, atualiza a senha e concede a permissão de administrador a essa conta. Depois, acesse **http://127.0.0.1:5000/admin** e entre com o e-mail e a senha definidos em `admin.env`.

**Importante:** mantenha o arquivo `admin.env` privado. Ele já está listado no `.gitignore` para evitar que suas credenciais sejam enviadas ao Git.

No painel é possível criar usuários, conceder/remover permissões administrativas, excluir contas e cadastrar títulos. Para publicar um título, envie um arquivo de vídeo (MP4, WebM, OGG ou MOV); a capa é opcional e, se não for enviada, o sistema usa uma arte padrão. Os arquivos enviados ficam em `static/uploads/`. Na lista do catálogo, você também pode ocultar ou reexibir títulos, anexar vídeos aos títulos que estavam aguardando arquivo e escolher qual título aparece em destaque no topo da página inicial.

A Biblioteca e as páginas de reprodução exibem somente títulos marcados como visíveis e que tenham um endereço de vídeo cadastrado. Títulos sem vídeo ficam no painel com a indicação “Aguardando vídeo”; ao anexar um arquivo, eles passam a ficar disponíveis. O administrador pode ocultar e reexibir títulos com vídeo sem excluí-los. A página inicial mostra um título em banner grande: usa o destaque escolhido no painel ou, se nenhum estiver escolhido, o título visível mais recente.

### Vídeos de demonstração e licenças

O projeto inclui três vídeos de demonstração dos projetos abertos da Blender Foundation: **Big Buck Bunny** (CC BY 3.0), **Sintel** (CC BY 3.0) e **Elephants Dream** (CC BY 2.5). Eles não são obras em domínio público: são distribuídos sob licenças Creative Commons, que exigem manter os créditos e cumprir as condições da licença. Os créditos e links oficiais estão em `videos_demo.py` e `static/videos/CREDITOS.md`.

> **Dica:** para não digitar o caminho toda vez, ative o ambiente uma vez com `.venv\Scripts\activate` (Linux/Mac: `source .venv/bin/activate`). Depois é só usar `python app.py` e `python scripts/init_db.py`.

### Sobre o `.venv`

A pasta `.venv` **não vai no projeto nem no GitHub**: ela é criada em cada computador (passo 1). Um `.venv` copiado de outro computador guarda o caminho do Python de quem o criou e não funciona fora de lá. Se der erro no ambiente, apague a pasta `.venv` e refaça o passo 1.

---

## Como usar

1. Entre com a sua conta.
2. Navegue com as **setas** e **Enter**.
3. Escolha um título e aperte **Assistir**.
4. Ao voltar depois, o botão vira **Retomar de mm:ss**.

**Atalhos do player**

| Tecla | Ação |
|---|---|
| `Espaço` ou `K` | Pausar e continuar |
| `←` `→` | Voltar e avançar 10 segundos |
| `↑` `↓` | Volume |
| `F` | Tela cheia |
| `M` | Mudo |
| `Esc` ou `Backspace` | Voltar ao título |

---

## Estrutura do projeto

```
VisionBox/
├── app.py          rotas do sistema (Flask)
├── config.py       lê o arquivo .env
├── database.py     conexão com o MySQL
├── models.py       consultas ao banco (uma classe por tabela)
├── videos_demo.py  trailers de demonstração
├── requirements.txt  dependências
├── .env            configurações (senha do banco) — não vai para o GitHub
├── .env.example    modelo do .env — este vai para o GitHub
├── db/             schema.sql (tabelas), seed.sql (catálogo), reset.sql
├── scripts/        init_db.py, adicionar_videos.py, gerar_capas.py
├── templates/      páginas HTML
└── static/         css, js, imagens e vídeos
```

---

## Banco de dados

Banco `visionbox`, com 5 tabelas:

| Tabela | O que guarda |
|---|---|
| `usuarios` | nome, e-mail e senha (em hash) |
| `titulos` | filmes, séries, documentários e shows, com capa, banner e vídeo |
| `progresso` | em que segundo cada usuário parou em cada título |
| `favoritos` | a "Minha lista" de cada usuário |
| `visualizacoes` | histórico do que cada usuário assistiu |

**Comandos úteis**

```bat
.venv\Scripts\python.exe scripts\init_db.py            :: cria o que faltar
.venv\Scripts\python.exe scripts\init_db.py --reset    :: apaga tudo e recria (apaga as contas)
.venv\Scripts\python.exe scripts\adicionar_videos.py   :: acrescenta os trailers a um banco já pronto
```

---

## Adicionar ou trocar imagens e vídeos

Tudo fica na tabela `titulos`, nas colunas `capa_url`, `banner_url` e `video_url`. Pode ser um arquivo local do projeto ou um link `https://...`.

```sql
UPDATE titulos SET video_url='/static/videos/meu-filme.mp4' WHERE id=1;
```

Coloque o arquivo MP4 em `static/videos`. Títulos sem `video_url` tocam um vídeo de demonstração.

**Vídeos que já vêm no projeto:** trailers de *Big Buck Bunny*, *Sintel* e *Elephants Dream*, dos projetos abertos do Blender. São trailers, não os filmes completos.

---

## Configuração (.env)

| Variável | Para que serve |
|---|---|
| `SECRET_KEY` | Chave de segurança da sessão (use um texto longo e aleatório) |
| `DB_HOST` | Onde está o MySQL (`localhost` se for no mesmo computador) |
| `DB_PORT` | Porta do MySQL (`3306`) |
| `DB_USER` | Usuário do MySQL |
| `DB_PASSWORD` | Senha do MySQL |
| `DB_NAME` | Nome do banco (`visionbox`) |

Depois de mexer no `.env`, reinicie o app.

**Ao enviar para o GitHub:** não envie o `.env`, porque ele tem a senha do banco. Envie só o `.env.example`, com valores de exemplo. O `.gitignore` já deixa o `.env` e o `.venv` de fora.

---

## Segurança

- Senhas guardadas com hash, nunca em texto puro.
- Proteção contra ataques CSRF em todos os formulários.
- Consultas ao banco sempre parametrizadas (protege contra SQL injection).
- Só o usuário logado acessa as páginas do catálogo.

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `Access denied for user` | Confira `DB_USER` e `DB_PASSWORD` no `.env`. |
| `Can't connect to MySQL server` | Ligue o serviço do MySQL. |
| Erro no ambiente do Python | Apague a pasta `.venv` e refaça o passo 1 de "Primeira vez". |
| "Python não encontrado" | Instale o Python 3.10+ e marque "Add python.exe to PATH". |
| Erro 400 ao enviar um formulário | Recarregue a página e tente de novo. |
| O vídeo não carrega | Confira o caminho em `video_url` e se o MP4 está em `static/videos`. |
| A página aparece desatualizada | Aperte `Ctrl + F5`. |
| Mudei o `.env` e nada mudou | Reinicie o app. |

---

## Identidade visual

| Cor | Código |
|---|---|
| Vermelho | `#FF2D3F` |
| Vinho | `#7A0A14` |
| Preto | `#000000` |
| Grafite | `#141414` |
| Branco gelo | `#F4F4F5` |

Fontes da marca: **Space Grotesk** (títulos) e **Inter** (texto). A interface usa um visual de TV neutro, inspirado no Apple TV (`static/css/tv.css`).

---

## Créditos

- Trailers de *Big Buck Bunny* e *Sintel* © Blender Foundation (CC BY 3.0). Teaser de *Elephants Dream* © Blender Foundation / Netherlands Media