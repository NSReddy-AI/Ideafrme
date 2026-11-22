import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
export const runtime = 'nodejs';
export async function DELETE(_req:Request,{params}:{params:Promise<{id:string}>}){const {id}=await params;try{await db.idea.delete({where:{id}});return new NextResponse(null,{status:204});}catch{return NextResponse.json({error:'Idea not found or database unavailable'},{status:404});}}
