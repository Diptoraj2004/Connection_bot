const jwt = require('jsonwebtoken');
const User = require('../models/User');

const genToken = (id) => jwt.sign({id}, process.env.JWT_SECRET, { expiresIn: process.env.JWT_EXPIRE });

exports.register = async (req,res) => {
  const { name,email,password,role,phone,studentId,university,year,licenseNumber,specialization,experience,instituteName,position } = req.body;
  let userData = {name,email,password,role,phone};
  if(role==='student') userData={...userData,studentId,university,year};
  if(role==='counselor') userData={...userData,licenseNumber,specialization,experience};
  if(role==='admin') userData={...userData,instituteName,position};
  const exists = await User.findOne({email});
  if(exists) return res.status(400).json({message:'User already exists'});
  const user = await User.create(userData);
  const token = genToken(user._id);
  res.status(201).json({ success:true, token, user:{ id:user._id,name:user.name,email:user.email,role:user.role }});
};

exports.login = async (req,res) => {
  const { email,password } = req.body;
  if(!email||!password) return res.status(400).json({message:'Provide email and password'});
  const user = await User.findOne({email}).select('+password');
  if(!user || !(await user.matchPassword(password)))
    return res.status(401).json({message:'Invalid credentials'});
  user.lastLogin = Date.now();
  await user.save();
  const token = genToken(user._id);
  res.json({ success:true, token, user:{ id:user._id,name:user.name,email:user.email,role:user.role }});
};

exports.getMe = async (req,res) => {
  res.json({ success:true, user:req.user });
};