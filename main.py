from fastapi import FastAPI
import motor.motor_asyncio
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.school_blog

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class BlogPostModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    content: str
    author: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

@app.post("/blog", response_model=BlogPostModel)
async def create_blog_post(blog_post: BlogPostModel):
    blog_post = jsonable_encoder(blog_post)
    new_blog_post = await db["blog_posts"].insert_one(blog_post)
    created_blog_post = await db["blog_posts"].find_one({"_id": new_blog_post.inserted_id})
    return created_blog_post

@app.get("/blog", response_model=List[BlogPostModel])
async def get_blog_posts():
    blog_posts = await db["blog_posts"].find().to_list(1000)
    return blog_posts

@app.get("/blog/{id}", response_model=BlogPostModel)
async def get_blog_post(id: str):
    blog_post = await db["blog_posts"].find_one({"_id": ObjectId(id)})
    if blog_post is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return blog_post

@app.put("/blog/{id}", response_model=BlogPostModel)
async def update_blog_post(id: str, blog_post: BlogPostModel):
    blog_post = jsonable_encoder(blog_post)
    updated_blog_post = await db["blog_posts"].update_one({"_id": ObjectId(id)}, {"$set": blog_post})
    if updated_blog_post.modified_count == 1:
        updated_blog_post = await db["blog_posts"].find_one({"_id": ObjectId(id)})
        if updated_blog_post is not None:
            return updated_blog_post
    existing_blog_post = await db["blog_posts"].find_one({"_id": ObjectId(id)})
    if existing_blog_post is not None:
        return existing_blog_post
    raise HTTPException(status_code=404, detail="Blog post not found")

@app.delete("/blog/{id}")
async def delete_blog_post(id: str):
    delete_result = await db["blog_posts"].delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return {"message": "Blog post deleted"}
    raise HTTPException(status_code=404, detail="Blog post not found")
