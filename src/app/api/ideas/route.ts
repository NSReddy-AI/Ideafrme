import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { ideaSchema } from '@/lib/validation';
export const runtime = 'nodejs';
export async function GET(){try{return NextResponse.json(await db.idea.findMany({include:{plans:{orderBy:{createdAt:'desc'}}},orderBy:{updatedAt:'desc'}}));}catch{return NextResponse.json({error:'Database unavailable'},{status:503});}}
export async function POST(req:Request){let body:unknown;try{body=await req.json();}catch{return NextResponse.json({error:'Invalid JSON'},{status:400});}const parsed=ideaSchema.safeParse(body);if(!parsed.success)return NextResponse.json({error:'Title must be 1–120 characters and description 10–5000 characters'},{status:400});try{return NextResponse.json(await db.idea.create({data:parsed.data}),{status:201});}catch{return NextResponse.json({error:'Database unavailable'},{status:503});}}
