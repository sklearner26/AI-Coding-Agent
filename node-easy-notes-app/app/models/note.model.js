const mongoose = require('mongoose');

const NoteSchema = mongoose.Schema({
    title: String,
    content: String,
    category: String,
    tags: [{ type: String }]
}, {
    timestamps: true
});

module.exports = mongoose.model('Note', NoteSchema);