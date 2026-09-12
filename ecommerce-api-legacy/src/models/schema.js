'use strict';

/**
 * Schema e dados iniciais.
 *
 * Antes estavam embutidos como strings em AppManager.js:10-23, disparados sem verificação de
 * erro. Agora são um módulo próprio, com erros propagados e chaves estrangeiras declaradas.
 */

const DDL = [
  `CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      pass TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      price REAL NOT NULL,
      active INTEGER NOT NULL DEFAULT 1
  )`,
  `CREATE TABLE IF NOT EXISTS enrollments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id),
      course_id INTEGER NOT NULL REFERENCES courses(id)
  )`,
  `CREATE TABLE IF NOT EXISTS payments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
      amount REAL NOT NULL,
      status TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      action TEXT NOT NULL,
      created_at DATETIME NOT NULL
  )`,
];

async function criarSchema(db) {
  for (const comando of DDL) {
    await db.run(comando);
  }
}

/**
 * Popula o banco quando vazio. A senha do usuário de exemplo entra como hash — antes
 * (AppManager.js:18) era gravada em texto puro.
 */
async function popularDadosIniciais(db, gerarHash) {
  const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
  if (total > 0) return;

  await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
    'Leonan',
    'leonan@fullcycle.com.br',
    await gerarHash('123'),
  ]);
  await db.run(
    'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
    ['Clean Architecture', 997.0, 'Docker', 497.0],
  );
  await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', [
    'PAID',
  ]);
}

module.exports = { criarSchema, popularDadosIniciais };
