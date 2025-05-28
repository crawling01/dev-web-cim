// server.js
const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const db = require('./db');

const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// Endpoint: Ambil data dari database (contoh admin)
app.get('/api/admin', (req, res) => {
  db.query('SELECT * FROM admin', (err, result) => {
    if (err) return res.status(500).send(err);
    res.json(result);
  });
});

// Endpoint: Ambil data dari services.json
app.get('/api/services', (req, res) => {
  const servicesDataPath = path.join(__dirname, 'data', 'services.json');

  fs.readFile(servicesDataPath, 'utf-8', (err, data) => {
    if (err) {
      console.error('Gagal membaca services.json:', err);
      return res.status(500).json({ error: 'Gagal membaca services.json' });
    }

    try {
      const services = JSON.parse(data);
      res.json(services);
    } catch (parseErr) {
      console.error('Gagal parsing JSON:', parseErr);
      res.status(500).json({ error: 'Gagal parsing JSON' });
    }
  });
});

// Tambahkan endpoint-endpoint berikut:

// GET team members
app.get('/api/team-members', (req, res) => {
    const query = `
        SELECT m.id, m.file_path, u.name, u.role as position, 
               CASE 
                   WHEN u.role = 'admin' OR u.role = 'team_lead' THEN 'Team Leads'
                   WHEN u.role = 'designer' THEN 'Visual Designers'
                   ELSE 'Creatives'
               END as category,
               TRUE as is_active,
               0 as display_order
        FROM media m
        JOIN users u ON m.uploaded_by = u.id
        WHERE m.file_type LIKE 'image/%'
        ORDER BY category, u.name
    `;
    
    db.query(query, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// POST new team member (via media upload)
app.post('/api/team-members', async (req, res) => {
    // Anggap sudah ada endpoint upload media
    res.status(501).json({ message: 'Please use media upload endpoint first' });
});

// PUT update team member
app.put('/api/team-members/:id', (req, res) => {
    const { id } = req.params;
    const { name, position, category, photo_url, is_active, display_order } = req.body;
    
    // Update user data
    db.query(
        'UPDATE users SET name = ?, role = ? WHERE id = (SELECT uploaded_by FROM media WHERE id = ?)',
        [name, position, id],
        (err) => {
            if (err) return res.status(500).json({ error: err.message });
            
            // Update media data if photo_url is provided
            if (photo_url) {
                db.query(
                    'UPDATE media SET file_path = ? WHERE id = ?',
                    [photo_url, id],
                    (err) => {
                        if (err) return res.status(500).json({ error: err.message });
                        res.json({ message: 'Member updated successfully' });
                    }
                );
            } else {
                res.json({ message: 'Member updated successfully' });
            }
        }
    );
});

// DELETE team member
app.delete('/api/team-members/:id', (req, res) => {
    const { id } = req.params;
    
    db.query('DELETE FROM media WHERE id = ?', [id], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Member deleted successfully' });
    });
});

// Upload media endpoint (untuk upload foto profil)
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });

app.post('/api/media/upload', upload.single('file'), (req, res) => {
    // Simpan file dan kembalikan path-nya
    const filePath = `/uploads/${req.file.filename}`;
    
    // Simpan ke database
    db.query(
        'INSERT INTO media (file_name, file_path, file_type, uploaded_by) VALUES (?, ?, ?, ?)',
        [req.file.originalname, filePath, req.file.mimetype, 1], // uploaded_by = 1 (admin)
        (err) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ filePath });
        }
    );
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
