import re
import pathlib
import sys

ROOT_PATH = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(ROOT_PATH.parent))

from email_subscriber.config import DB_URL, SUBSCRIBER_MASK
from email_subscriber.subscriberDB import EmailSubscriberDB, Platform, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text


def main():
    print("开始清理不合规的订阅邮箱...")
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    pattern = re.compile(SUBSCRIBER_MASK)
    all_subs = session.query(EmailSubscriberDB).all()
    invalid = [s for s in all_subs if not pattern.match(s.email)]
    print(f"共找到 {len(invalid)} 个不合规邮箱：")
    for s in invalid:
        print(f" - {s.email}")

    if not invalid:
        print("没有需要删除的邮箱。")
        session.close()
        return

    confirm = input("确认删除这些邮箱吗？(y/N): ").strip().lower()
    if confirm != "y":
        print("操作取消。")
        session.close()
        return

    for s in invalid:
        session.delete(s)
    session.commit()
    print("已删除不合规邮箱。")

    # 重新整理ID（sqlite3主键自增无法直接重排，通常不建议重排主键）
    # 但如确需连续，可以导出剩余数据，清空表，重建并插入
    # 下面是可选的重排方法（慎用！）
    do_reindex = input("需要重排订阅者ID使其连续吗？(y/N): ").strip().lower()
    if do_reindex == "y":
        # 导出剩余数据
        valid_subs = session.query(EmailSubscriberDB).all()
        subs_data = []
        for s in valid_subs:
            subs_data.append(
                {
                    "email": s.email,
                    "all_platforms": s.all_platforms,
                    "platform_ids": [p.id for p in s.platforms],
                }
            )
        # 清空表 - 使用text()包装SQL语句
        session.execute(text("DELETE FROM subscriber_platform"))
        session.execute(text("DELETE FROM email_subscribers"))
        session.commit()
        # 关闭session，重新开启以避免主键自增混乱
        session.close()
        session = Session()
        # 重新插入
        for sub in subs_data:
            new_sub = EmailSubscriberDB(
                email=sub["email"], all_platforms=sub["all_platforms"]
            )
            session.add(new_sub)
            session.commit()
            # 重新关联平台
            if not sub["all_platforms"]:
                platforms = (
                    session.query(Platform)
                    .filter(Platform.id.in_(sub["platform_ids"]))
                    .all()
                )
                new_sub.platforms = platforms
                session.commit()
        print("ID重排完成。")
    else:
        print("未进行ID重排。")

    session.close()
    print("清理完成。")


if __name__ == "__main__":
    main()
