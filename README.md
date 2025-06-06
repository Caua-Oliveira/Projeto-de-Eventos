# Como começar a rodar

1. Crie uma database no mysql com esse código:
```sql

CREATE DATABASE IF NOT EXISTS plataforma_events;
USE plataforma_events;

CREATE TABLE tipos_usuario (
    id_tipo_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO tipos_usuario (nome) 
VALUES ('participante'), ('organizador'), ('admin');


CREATE TABLE usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    id_tipo_usuario INT NOT NULL,
    FOREIGN KEY (id_tipo_usuario) 
        REFERENCES tipos_usuario(id_tipo_usuario)
);


CREATE TABLE events (
    id_evento INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT,
    local VARCHAR(150),
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    vagas INT NOT NULL DEFAULT 0,
    id_organizador INT NOT NULL,
    CHECK (data_fim >= data_inicio),
    FOREIGN KEY (id_organizador) 
        REFERENCES usuarios(id_usuario)
);
CREATE INDEX idx_events_organizador 
    ON events(id_organizador);


CREATE TABLE tipos_atividade (
    id_tipo_atividade INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO tipos_atividade (nome) 
VALUES ('palestra'), ('mesa-redonda'), ('oficina'), ('painel'), ('outro');

CREATE TABLE atividades (
    id_atividade INT PRIMARY KEY AUTO_INCREMENT,
    id_evento INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT,
    data_hora DATETIME NOT NULL,
    duracao_minutos INT CHECK (duracao_minutos > 0),
    id_tipo_atividade INT NOT NULL,
    FOREIGN KEY (id_evento) 
        REFERENCES events(id_evento),
    FOREIGN KEY (id_tipo_atividade) 
        REFERENCES tipos_atividade(id_tipo_atividade)
);
CREATE INDEX idx_atividades_evento 
    ON atividades(id_evento);


CREATE TABLE inscricoes_evento (
    id_inscricao_evento INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario          INT NOT NULL,
    id_evento           INT NOT NULL,
    data_inscricao      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_evento) 
        REFERENCES events(id_evento),
    UNIQUE (id_usuario, id_evento)
);
CREATE INDEX idx_inscricoes_evento_usuario 
    ON inscricoes_evento(id_usuario);
CREATE INDEX idx_inscricoes_evento_evento  
    ON inscricoes_evento(id_evento);


CREATE TABLE convidados (
    id_convidado INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    bio TEXT,
    foto VARCHAR(255)
);

CREATE TABLE convidados_events (
    id_evento   INT NOT NULL,
    id_convidado INT NOT NULL,
    papel VARCHAR(100),
    PRIMARY KEY (id_evento, id_convidado),
    FOREIGN KEY (id_evento)   
        REFERENCES events(id_evento),
    FOREIGN KEY (id_convidado) 
        REFERENCES convidados(id_convidado)
);


CREATE TABLE certificados (
    id_certificado INT PRIMARY KEY AUTO_INCREMENT,
    id_inscricao_evento INT NOT NULL,
    url_arquivo VARCHAR(255),
    data_emissao DATE,
    FOREIGN KEY (id_inscricao_evento) 
        REFERENCES inscricoes_evento(id_inscricao_evento)
);


CREATE TABLE avaliacoes (
    id_avaliacao INT PRIMARY KEY AUTO_INCREMENT,
    id_inscricao_evento INT NOT NULL,
    nota INT CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    FOREIGN KEY (id_inscricao_evento) 
        REFERENCES inscricoes_evento(id_inscricao_evento)
);


DELIMITER //
DROP FUNCTION IF EXISTS tem_vagas_evento;
CREATE FUNCTION tem_vagas_evento(pid_evento INT) 
RETURNS TINYINT(1) 
DETERMINISTIC
BEGIN
    DECLARE vagas_totais     INT;
    DECLARE total_inscricoes INT;
    
    SELECT vagas 
      INTO vagas_totais
      FROM events
     WHERE id_evento = pid_evento;
    
    IF vagas_totais IS NULL THEN
        RETURN 1;
    END IF;
    
    SELECT COUNT(*) 
      INTO total_inscricoes
      FROM inscricoes_evento
     WHERE id_evento = pid_evento;
    
    RETURN total_inscricoes < vagas_totais;
END //
DELIMITER ;


DELIMITER //
DROP PROCEDURE IF EXISTS registrar_inscricao_evento;
CREATE PROCEDURE registrar_inscricao_evento(
    IN pid_usuario INT,
    IN pid_evento  INT
)
BEGIN
    DECLARE disponivel TINYINT(1);
    SET disponivel = tem_vagas_evento(pid_evento);

    IF disponivel THEN
        INSERT INTO inscricoes_evento (id_usuario, id_evento)
        VALUES (pid_usuario, pid_evento);
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Não há vagas disponíveis para este evento.';
    END IF;
END //
DELIMITER ;


CREATE OR REPLACE VIEW resumo_atividades AS
SELECT 
    a.id_atividade,
    a.titulo,
    e.titulo AS evento,
    COUNT(v.id_inscricao_evento) AS total_inscritos_evento
FROM atividades a
JOIN events e 
  ON a.id_evento = e.id_evento
LEFT JOIN inscricoes_evento v 
  ON e.id_evento = v.id_evento
GROUP BY a.id_atividade, a.titulo, e.titulo;


CREATE OR REPLACE VIEW resumo_inscricoes_events AS
SELECT 
    e.id_evento,
    e.titulo AS evento,
    COUNT(ie.id_inscricao_evento) AS total_inscritos
FROM events e
LEFT JOIN inscricoes_evento ie 
  ON e.id_evento = ie.id_evento
GROUP BY e.id_evento, e.titulo;


CREATE OR REPLACE VIEW certificados_por_usuario AS
SELECT
    u.id_usuario,
    u.nome,
    e.titulo      AS evento,
    c.url_arquivo,
    c.data_emissao
FROM certificados c
JOIN inscricoes_evento ie 
  ON c.id_inscricao_evento = ie.id_inscricao_evento
JOIN usuarios u 
  ON ie.id_usuario = u.id_usuario
JOIN events e 
  ON ie.id_evento = e.id_evento;


DELIMITER //
DROP TRIGGER IF EXISTS trg_set_data_emissao_certificado;
CREATE TRIGGER trg_set_data_emissao_certificado
BEFORE INSERT ON certificados
FOR EACH ROW
BEGIN
    IF NEW.data_emissao IS NULL THEN
        SET NEW.data_emissao = CURDATE();
    END IF;
END //
DELIMITER ;


SET GLOBAL event_scheduler = ON;
DELIMITER //
DROP EVENT IF EXISTS evt_avaliacoes_padrao;
CREATE EVENT evt_avaliacoes_padrao
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    INSERT INTO avaliacoes (id_inscricao_evento, nota, comentario)
    SELECT ie.id_inscricao_evento, 5, 'Avaliação automática padrão'
    FROM inscricoes_evento ie
    JOIN events e 
      ON ie.id_evento = e.id_evento
    WHERE e.data_fim < CURDATE()
      AND NOT EXISTS (
          SELECT 1 
            FROM avaliacoes av 
           WHERE av.id_inscricao_evento = ie.id_inscricao_evento
      );
END //
DELIMITER ;
``` 
2. Clone o repositorio

3. Instale as dependências  
   ```bash
   pip install flask flask_sqlalchemy pymysql jinja2 werkzeug
   ```
4. Modifique o setup do SQLAlchemy
   ```py
   # Setup do flask e SQLAlchemy
    app = Flask(__name__)
    app.secret_key = 'secretkey'
    #Aqui onde está "1234" você coloca a senha que escolheu para o mysql.
    #Onde está "root" você coloca o usuario do mysql, normalmente é root mesmo, a não ser que você mudou.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/plataforma_events'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   ```
   
5. Rode o flask_app.py
   ```bash
    python flask_app.py
   ```
6. Quando você for cadastrar usuario, ele será um "participante", para cadastrar um "admin" faça isso no proprio workbench ou então mude o codigo de sign_up:
```py
def sign_up():
...
tipo = TipoUsuario.query.filter_by(
            nome='participante').first()  # Automaticamente registra o usuario como participante (só trocar participante por admin)
...
```
# Como funciona o código flask etc
Para criar uma página nova, precisa se criar uma rota:
```py
@app.route('/nome_da_pagina', methods=['GET', 'POST'])
def nome_da_pagina():
# o method será POST para quando botões tipo "Cadastrar" ou "Logar" forem clicados, ai no codigo abaixo faz o necessário para cadastrar
  if request.method == 'POST':
    #código que precisar
    return

  #quando for GET (padrão) só renderiza a página.
  return render_template('nome_da_pagina.html')
```
E com isso também precisa criar o html e o css. O html tem que ficar na pasta "templates" e o css na pasta "static" <br>
<br>
No html, para ser redirecionado à outra página, o href tem que ser isso:
```html
<a href="{{ url_for('nome_da_pagina') }}">Ir para página X</a>
```
No html também está sendo usado o Jinja, que permite criar codigos similares ao python dentro do html.
```html
#Exemplo dos events inscritos na pagina de profile:
<div class="events-inscritos">
        <h3>events Inscritos:</h3>
        {% if inscricoes %} 
        <ul>
          {% for ins in inscricoes %}
            <li>
              <a href="{{ url_for('event_details', event_id=ins.evento.id_evento) }}">
                {{ ins.evento.titulo }}
              </a>
            </li>
          {% endfor %}
        </ul>
        {% else %}
          <p>Você não está inscrito em nenhum evento.</p>
        {% endif %}
</div>
```
Tudo que tem {% ___ %} é do jinja e essas variaveis que estão sendo usadas vem da route:
```py
@app.route('/profile')
@necessita_login # Decorator para garantir que o usuário está logado antes de acessar o profile
def profile():
    user = usuario_logado()
    minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
    return render_template('profile.html', user=user, inscricoes=minhas_inscricoes) #no html o jinja usou inscricoes, que foi dado nesse return.
``` 
Para fazer as querys no banco de dados, faz o que foi mostrado acima:
```py
minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
evento = Evento.query.get_or_404(event_id)
usuario = Usuario.query.get(uid)
#IncricaoEvento, Evento, Usuario são as classes Modelos que estão em flask_app.py
```

# Frameworks
  1. Flask - Utilizado para o roteamento do site 
  2. SQLAlchemy - Utilizado junto ao pymysql para realizar as querys do banco de dados
  3. Pymysql - Utilizado junto ao SQLAlchemy para realizar as querys do banco de dados
  4. Werkzeug - Utilizado para incripitação de senha
  5. Jinja2 - Utilizado pelo flask para fazer HTMLs dinâmicos
