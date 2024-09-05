from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
604180
629918
630595
628595
627098
626391
624377
624268
623103
620851
618759
619555
618802
623269
617312
616107
616080
615063
614600
578569
612827
607101
526089
456911
601278
587716
242455
73401
504833
505530
318202
573991
546063
589343
587954
559047
515772
179163
576988
574796
189700
544401
571970
330459
524925
570399
568786
214305
567480
509898
512871
563770
563747
562146
562243
561959
394001
541597
561495
558026
557306
243908
554457
242738
137161
551529
1205
548696
523179
547273
545210
544526
544405
542239
542252
346609
501923
534682
531869
530493
528910
529481
527945
527930
527862
226784
524864
290085
524154
523642
523285
522480
521710
513348
518360
517703
517500
506489
511611
511850
514346
511010
496383
506966
503483
503136
503139
319853
502033
403099
501846
226538
499203
499797
498459
497689
497111
495255
251054
494324
487805
486733
209917
487026
487286
487298
474165
485816
254030
224412
483059
482653
481106
480713
479035
374565
475612
233985
473312
179160
378308
10187
467180
465141
295686
286355
418816
462243
461640
4794
278459
459036
180840
151696
455886
356980
398569
300993
359581
453931
453333
415008
452212
451269
86245
450085
398669
279371
448534
150462
381591
446025
445600
445794
442234
442179
441373
12067
278288
330239
389781
436319
435428
433834
433297
429987
429084
428646
425295
426268
368733
422806
419611
420028
225952
418514
301454
410272
417422
416888
291555
119562
414089
323365
412984
412295
411262
411759
411743
390353
206328
204367
410841
226333
376126
409856
408184
408328
407852
407063
399319
377954
400444
377441
396284
209918
278388
389479
382552
362057
384427
380460
332827
354967
346821
302216
339140
150901
285808
187512
44230
335927
149197
226647
144132
122494
222661
270555
243921
150590
173546
198024
62119
239676
245937
198027
229859
246118
244073
233362



'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
