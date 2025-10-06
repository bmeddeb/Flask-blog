# WordPress-Style Migration Guide

## 📋 What This Migration Does

Transforms your blog from a simple post/page structure to WordPress's unified content model:

### Before (Simple Blog)
```
blog_posts (posts only)
pages (static pages only)
```

### After (WordPress Style)
```
posts (everything: posts, pages, projects, etc.)
├── post_type = 'post'    → Blog posts
├── post_type = 'page'    → Static pages
└── post_type = 'project' → Projects (ready to use!)

post_types (register custom types)
post_meta (flexible custom fields)
```

## 🚀 Migration Steps

### Step 1: Backup Your Database
```bash
cp blog.db blog.db.backup
```

### Step 2: Run the Migration
```bash
python migrations/migrate_to_wordpress_style.py
```

The script will:
- ✅ Create `post_types` and `post_meta` tables
- ✅ Add `post_type`, `post_status`, `post_parent` columns
- ✅ Rename `blog_posts` → `posts`
- ✅ Migrate `pages` → `posts` with `post_type='page'`
- ✅ Move page metadata → `post_meta`
- ✅ Seed default post types (post, page, project)
- ✅ Drop old `pages` table

### Step 3: Update Your Code

#### Replace models.py
```bash
mv models.py models_old.py
mv models_new.py models.py
```

#### Update imports across the codebase:
```python
# OLD
from models import BlogPost, Page

# NEW
from models import Post, PostType, PostMeta
```

#### Update queries:
```python
# OLD: Get blog posts
BlogPost.query.filter_by(published=True).all()

# NEW: Get blog posts
Post.query.filter_by(post_type='post', post_status='publish').all()

# NEW: Get pages
Post.query.filter_by(post_type='page', post_status='publish').all()

# NEW: Get projects
Post.query.filter_by(post_type='project', post_status='publish').all()
```

### Step 4: Update Forms

Your forms need to support post types now. Example:

```python
class PostForm(FlaskForm):
    post_type = SelectField('Type', choices=[
        ('post', 'Blog Post'),
        ('page', 'Page'),
        ('project', 'Project')
    ])
    title = StringField('Title', validators=[DataRequired()])
    # ... rest of fields
```

### Step 5: Update Routes

```python
# Example: Blog listing
@bp.route('/blog')
def blog_list():
    posts = Post.query.filter_by(
        post_type='post',
        post_status='publish'
    ).order_by(Post.published_at.desc()).all()
    return render_template('blog_list.html', posts=posts)

# Example: Projects listing
@bp.route('/projects')
def projects_list():
    projects = Post.query.filter_by(
        post_type='project',
        post_status='publish'
    ).order_by(Post.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

# Example: Single post (any type)
@bp.route('/<slug>')
def single_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template('post.html', post=post)
```

### Step 6: Using PostMeta

```python
# Set custom field
post = Post.query.get(1)
post.set_meta('github_url', 'https://github.com/user/repo')
post.set_meta('demo_url', 'https://demo.com')
db.session.commit()

# Get custom field
github_url = post.get_meta('github_url')

# Get all meta
all_meta = post.get_all_meta()
# Returns: {'github_url': '...', 'demo_url': '...'}
```

## 📊 New Database Schema

### posts table
```sql
id, title, slug, content, excerpt, author
post_type          -- 'post', 'page', 'project', etc.
post_status        -- 'publish', 'draft', 'private', 'pending'
post_parent        -- For hierarchical content (parent page ID)
user_id, featured, category_id
created_at, updated_at, published_at
```

### post_types table
```sql
id, name, label, label_singular, description
hierarchical       -- Can have parent/child relationships
has_archive        -- Has archive page (/blog/, /projects/)
supports_categories, supports_tags
supports_excerpt, supports_featured_image
menu_icon, menu_position, show_in_menu
```

### post_meta table
```sql
id, post_id, meta_key, meta_value

-- Examples for Pages:
post_id=1, meta_key='layout', meta_value='full-width'
post_id=1, meta_key='show_in_nav', meta_value='1'

-- Examples for Projects:
post_id=5, meta_key='github_url', meta_value='https://...'
post_id=5, meta_key='tech_stack', meta_value='Python, Flask, SQLite'
```

## 🎯 Common Patterns

### Query by Post Type
```python
# Blog posts
Post.query.filter_by(post_type='post', post_status='publish').all()

# Pages
Post.query.filter_by(post_type='page', post_status='publish').all()

# Projects
Post.query.filter_by(post_type='project', post_status='publish').all()
```

### Hierarchical Pages
```python
# Get parent page
parent = Post.query.filter_by(slug='about', post_type='page').first()

# Get child pages
children = Post.query.filter_by(post_parent=parent.id).all()

# Or use relationship:
children = parent.children.all()
```

### Check Post Type Capabilities
```python
post_type = PostType.get_by_name('project')
if post_type.supports_categories:
    # Show category selector
    pass
```

## 🔄 Rollback (if needed)

If something goes wrong:

```bash
python migrations/migrate_to_wordpress_style.py --rollback
```

Or restore from backup:
```bash
rm blog.db
cp blog.db.backup blog.db
```

## ✅ Testing Checklist

After migration, test:

- [ ] Blog posts still display correctly
- [ ] Pages still work (check `/about`, etc.)
- [ ] Admin dashboard shows all posts
- [ ] Can create new blog posts
- [ ] Can create new pages
- [ ] Categories and tags work
- [ ] Post meta is saved/retrieved correctly
- [ ] Hierarchical pages work (if used)

## 🎉 New Capabilities

After migration, you can:

1. **Create Projects** - New post type ready to use
2. **Hierarchical Pages** - Pages can have sub-pages
3. **Custom Fields** - Add any metadata via PostMeta
4. **Flexible Content Types** - Add testimonials, portfolios, etc.
5. **Post Status Control** - draft, publish, private, pending
6. **Archive Pages** - Automatic `/projects/` listing

## 🔧 Adding New Post Types

Want to add "Portfolio" or "Testimonials"?

```python
# 1. Add to database
db.session.add(PostType(
    name='portfolio',
    label='Portfolio Items',
    label_singular='Portfolio Item',
    hierarchical=False,
    has_archive=True,
    supports_tags=True,
    menu_icon='iconoir-folder'
))
db.session.commit()

# 2. Create posts with post_type='portfolio'
post = Post(
    title='My Project',
    slug='my-project',
    content='...',
    post_type='portfolio',
    post_status='publish'
)
db.session.add(post)
db.session.commit()

# 3. Add custom fields
post.set_meta('client_name', 'Acme Corp')
post.set_meta('project_url', 'https://...')
db.session.commit()

# 4. Create route
@app.route('/portfolio')
def portfolio():
    items = Post.query.filter_by(
        post_type='portfolio',
        post_status='publish'
    ).all()
    return render_template('portfolio.html', items=items)
```

## 📚 WordPress Equivalents

| WordPress | Your App |
|-----------|----------|
| `wp_posts` | `posts` |
| `wp_postmeta` | `post_meta` |
| `get_post_meta()` | `post.get_meta('key')` |
| `update_post_meta()` | `post.set_meta('key', 'value')` |
| `get_posts(['post_type' => 'post'])` | `Post.query.filter_by(post_type='post')` |
| `register_post_type()` | Add row to `post_types` table |

## 🆘 Troubleshooting

### Error: "no such table: posts"
- Migration didn't complete. Run it again or restore backup.

### Error: "no such column: post_type"
- The `posts` table wasn't updated. Check Step 2 of migration.

### Posts not showing
- Check `post_status` - should be 'publish' not just True
- Update query: `.filter_by(post_status='publish')`

### Page metadata missing
- Check `post_meta` table
- Use `post.get_meta('layout')` instead of `post.layout`

## 📞 Support

If you encounter issues:
1. Check your backup: `ls -lh blog.db*`
2. Review migration logs
3. Check database: `sqlite3 blog.db ".schema posts"`
4. Test queries: `sqlite3 blog.db "SELECT post_type, COUNT(*) FROM posts GROUP BY post_type"`

Happy migrating! 🚀
