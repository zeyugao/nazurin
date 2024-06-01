
from pybooru import Danbooru
import os


class MyDanbooru(Danbooru):
    def upload_create(self, files):
        file_ = {}
        for idx, file in enumerate(files):
            file_[f'upload[files][{idx}]'] = (
                os.path.basename(file), open(file, 'rb'))
        return self._get('uploads.json', {}, 'POST', auth=True,
                         file_=file_)

    def post_create(
        self,
        media_asset_id,
        upload_media_asset_id,
        tag_string, source,
        artist_commentary_title,
        artist_commentary_desc,
        translated_commentary_title='',
        translated_commentary_desc='',
        parent_id='',
        rating='g',
        is_pending=0
    ):
        params = {
            'media_asset_id': media_asset_id,
            'upload_media_asset_id': upload_media_asset_id,
            'post[rating]': rating,
            'post[tag_string]': tag_string,
            'post[is_pending]': is_pending,
            'post[source]': source,
            'post[artist_commentary_title]': artist_commentary_title,
            'post[artist_commentary_desc]': artist_commentary_desc,
            'post[translated_commentary_title]': translated_commentary_title,
            'post[translated_commentary_desc]': translated_commentary_desc,
            'post[parent_id]': parent_id,
        }
        return self._get('posts.json', params, 'POST', auth=True)

    def artist_create(self, name, other_names=None, group_name=None,
                      url_string=None, body=None):
        """Function to create an artist (Requires login) (UNTESTED).

        Parameters:
            name (str):
            other_names (str): List of alternative names for this
                                     artist, comma delimited.
            group_name (str): The name of the group this artist belongs to.
            url_string (str): List of URLs associated with this artist,
                              whitespace or newline delimited.
            body (str): DText that will be used to create a wiki entry at the
                        same time.
        """
        params = {
            'artist[name]': name,
            'artist[other_names]': other_names,
            'artist[group_name]': group_name,
            'artist[url_string]': url_string,
            'artist[body]': body,
        }

        return self._get('artists.json', params, method='POST', auth=True)

    def bulk_upload_then_post(
        self, files, tags, source,
        artist_commentary_title,
        artist_commentary_desc,
        translated_commentary_title='',
        translated_commentary_desc='',
    ):
        upload_res = self.upload_create(
            files=files,
        )
        upload_id = upload_res['id']
        upload_detail = self.upload_show(upload_id)

        parent_post = None

        for cur_upload_media_asset in upload_detail['upload_media_assets']:
            upload_media_asset_id = cur_upload_media_asset['id']
            media_asset_id = cur_upload_media_asset['media_asset_id']

            try:
                post_create_res = self.post_create(
                    media_asset_id=media_asset_id,
                    upload_media_asset_id=upload_media_asset_id,
                    tag_string=' '.join(tags),
                    source=source,
                    artist_commentary_title=artist_commentary_title,
                    artist_commentary_desc=artist_commentary_desc,
                    translated_commentary_title=translated_commentary_title,
                    translated_commentary_desc=translated_commentary_desc,
                    parent_id=parent_post or '',
                )
                post_id = post_create_res['id']

                if parent_post is None:
                    parent_post = post_id
            except Exception as e:
                print(
                    f'Create Post failed: upload_id: {upload_detail["id"]}, media_asset_id: {media_asset_id}, upload_media_asset_id: {upload_media_asset_id}')
                print(e)
