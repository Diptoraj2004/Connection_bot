const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  name: { type: String, required: true, maxlength: 50 },
  email: {
    type: String, required: true, unique: true,
    match: [/\S+@\S+\.\S+/, 'Invalid email']
  },
  password: { type: String, required: true, minlength: 6, select: false },
  role: {
    type: String, enum: ['student','counselor','admin'], required: true
  },
  phone: String,
  // Student fields
  studentId: { type: String, required: function(){ return this.role==='student'; } },
  university:{ type:String, required: function(){return this.role==='student';} },
  year: { type:Number, required: function(){return this.role==='student';} },
  // Counselor fields
  licenseNumber:{ type:String, required:function(){return this.role==='counselor';} },
  specialization:{ type:[String], required:function(){return this.role==='counselor';} },
  experience:{ type:Number, required:function(){return this.role==='counselor';} },
  // Admin fields
  instituteName:{ type:String, required:function(){return this.role==='admin';} },
  position:{ type:String, required:function(){return this.role==='admin';} },
  isVerified:{ type:Boolean, default:false },
  createdAt:{ type:Date, default:Date.now },
  lastLogin:Date
});

// Hash password
userSchema.pre('save', async function(next){
  if(!this.isModified('password')) return next();
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
  next();
});

// Match password
userSchema.methods.matchPassword = async function(entered){
  return await bcrypt.compare(entered, this.password);
};

module.exports = mongoose.model('User', userSchema);