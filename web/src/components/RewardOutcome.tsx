import type {AnswerResult} from '../lib/api'
export default function RewardOutcome({reward}:{reward:AnswerResult['reward']}){
 if(!reward)return null
 const labels:Record<string,string>={awarded:`+${reward.xp} XP · +${reward.points} reward point`,already_rewarded:'You already earned XP for this question.',daily_cap:'Daily XP limit reached; your practice was saved.',guest:'Sign in to earn XP on future verified-key answers.',unofficial:'Practice saved. Question XP requires an official key.',incorrect:'Practice saved. A correct verified-key answer can earn XP.',ineligible:'Practice saved; this answer is not eligible for XP.'}
 return <p className="mt-2 text-[12px] text-secondary">{labels[reward.status]||'Practice saved.'}</p>
}
