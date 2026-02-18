from nicegui import ui
from src.ui.layout import MainLayout
from src.ui.registry import ui_registry, AppMetadata
from src.core.hooks import hookimpl
from .models import BlogPost
from slugify import slugify
from loguru import logger

@ui.page("/blogger")
async def blog_list_page():
    with MainLayout():
        ui.label("Blogger Portal").classes("text-3xl font-black")
        ui.label("Latest insights and community updates.").classes("text-slate-500 mb-8")

        posts = await BlogPost.find(BlogPost.status == "published").to_list()
        
        if not posts:
            ui.label("No posts yet. Login as admin to create one!").classes("italic text-slate-400")
        
        with ui.grid(columns=1).classes("w-full max-w-3xl gap-6"):
            for post in posts:
                with ui.card().classes("w-full cursor-pointer hover:shadow-lg transition-shadow").on("click", lambda p=post: ui.navigate.to(f"/blogger/post/{p.slug}")):
                    with ui.column().classes("p-4 gap-2"):
                        ui.label(post.title).classes("text-xl font-bold text-primary")
                        if post.summary:
                            ui.label(post.summary).classes("text-sm text-slate-600")
                        ui.label(f"Published on {post.created_at.strftime('%Y-%m-%d')}").classes("text-xs text-slate-400")

        # Admin Button
        ui.button("Go to Editor", icon="edit", on_click=lambda: ui.navigate.to("/blogger/admin")).classes("fixed-bottom-right m-8").props("elevated rounded color=secondary")

@ui.page("/blogger/post/{slug}")
async def blog_post_page(slug: str):
    post = await BlogPost.get_by_slug(slug)
    with MainLayout():
        if not post:
            ui.label("Post not found").classes("text-red-500")
            ui.button("Back to List", on_click=lambda: ui.navigate.to("/blogger"))
            return

        with ui.column().classes("w-full max-w-4xl mx-auto p-8 gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/blogger")).props("flat")
            ui.label(post.title).classes("text-4xl font-black")
            ui.label(f"Created at {post.created_at}").classes("text-sm text-slate-400 border-b pb-4 w-full")
            
            # Render HTML content
            ui.html(post.content).classes("prose lg:prose-xl")

@ui.page("/blogger/admin")
async def blog_admin_page():
    # In a real app, check auth here. For demo, we just show it.
    with MainLayout():
        ui.label("Blog Content Manager").classes("text-3xl font-black")
        
        with ui.row().classes("w-full gap-4 mt-8"):
            title_input = ui.input("Title", placeholder="Enter post title...").classes("flex-grow")
            status_select = ui.select(options=["draft", "published"], value="draft", label="Status").classes("w-32")
        
        with ui.row().classes("w-full gap-2 mb-2"):
            from src.ui.components.file_picker import FilePicker
            def on_file_picked(url):
                content_editor.value += f'<img src="{url}" style="max-width:100%; border-radius:8px;" />'
                ui.notify(f"Inserted image: {url}")
            
            ui.button("Add Image", icon="image", on_click=lambda: FilePicker(on_file_picked).open()).props("outline color=secondary")

        content_editor = ui.editor(placeholder="Write your story here...").classes("w-full h-96")
        
        async def save_post():
            if not title_input.value or not content_editor.value:
                ui.notify("Title and content are required", type="warning")
                return
            
            slug = slugify(title_input.value)
            post = BlogPost(
                title=title_input.value,
                slug=slug,
                content=content_editor.value,
                status=status_select.value
            )
            try:
                await post.insert()
                ui.notify("Post saved successfully!", type="positive")
                ui.navigate.to("/blogger")
            except Exception as e:
                logger.error(f"Failed to save post: {e}")
                ui.notify("Error: Title (slug) must be unique.", type="negative")

        ui.button("Publish Post", icon="send", on_click=save_post).classes("mt-4").props("elevated")

@hookimpl
def register_ui():
    """Register the Blogger App."""
    ui_registry.register_app(AppMetadata(
        name="Blogger",
        icon="article",
        route="/blogger",
        description="Write and publish content to your people.",
        commands=["new post", "edit blog", "view feed"]
    ))
